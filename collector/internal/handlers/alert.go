// Alert webhook handler for KAM Collector service
package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"kam-collector/internal/database"
	"kam-collector/internal/models"
	"kam-collector/internal/redis"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type AlertHandler struct {
	db     *database.DB
	redis  *redis.Client
	logger *logrus.Logger
}

func NewAlertHandler(db *database.DB, redis *redis.Client, logger *logrus.Logger) *AlertHandler {
	return &AlertHandler{
		db:     db,
		redis:  redis,
		logger: logger,
	}
}

func (h *AlertHandler) HandleWebhook(c *gin.Context) {
	var webhook models.AlertWebhook
	
	if err := c.ShouldBindJSON(&webhook); err != nil {
		h.logger.WithError(err).Error("Failed to parse webhook payload")
		c.JSON(http.StatusBadRequest, models.AlertResponse{
			Success: false,
			Message: "Invalid JSON payload",
			Error:   err.Error(),
		})
		return
	}

	h.logger.WithFields(logrus.Fields{
		"receiver":    webhook.Receiver,
		"status":      webhook.Status,
		"alert_count": len(webhook.Alerts),
	}).Info("Received alert webhook")

	var processedAlerts []string
	var errors []string

	for _, alertData := range webhook.Alerts {
		alertID, err := h.processAlert(c.Request.Context(), webhook, alertData)
		if err != nil {
			h.logger.WithError(err).Error("Failed to process alert")
			errors = append(errors, err.Error())
			continue
		}
		processedAlerts = append(processedAlerts, alertID)
	}

	if len(errors) > 0 && len(processedAlerts) == 0 {
		c.JSON(http.StatusInternalServerError, models.AlertResponse{
			Success: false,
			Message: "Failed to process all alerts",
			Error:   fmt.Sprintf("Errors: %v", errors),
		})
		return
	}

	response := models.AlertResponse{
		Success: true,
		Message: fmt.Sprintf("Processed %d alerts", len(processedAlerts)),
	}

	if len(errors) > 0 {
		response.Message += fmt.Sprintf(" with %d errors", len(errors))
	}

	c.JSON(http.StatusOK, response)
}

func (h *AlertHandler) processAlert(ctx context.Context, webhook models.AlertWebhook, alertData models.AlertData) (string, error) {
	// Generate external ID from fingerprint or create one
	externalID := alertData.Fingerprint
	if externalID == "" {
		externalID = uuid.New().String()
	}

	// Determine severity from labels
	severity := h.extractSeverity(alertData.Labels)
	
	// Extract title from labels or annotations
	title := h.extractTitle(alertData.Labels, alertData.Annotations)

	// Create alert model
	alert := &models.Alert{
		ID:           uuid.New(),
		ExternalID:   externalID,
		Source:       webhook.Receiver,
		Severity:     severity,
		Title:        title,
		Description:  h.extractDescription(alertData.Annotations),
		Labels:       alertData.Labels,
		Annotations:  alertData.Annotations,
		StartsAt:     alertData.StartsAt,
		EndsAt:       alertData.EndsAt,
		GeneratorURL: alertData.GeneratorURL,
		Fingerprint:  alertData.Fingerprint,
		Status:       alertData.Status,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	// Serialize raw data
	rawData, err := json.Marshal(alertData)
	if err != nil {
		return "", fmt.Errorf("failed to serialize raw data: %w", err)
	}
	alert.RawData = rawData

	// Validate alert
	if err := alert.Validate(); err != nil {
		return "", fmt.Errorf("alert validation failed: %w", err)
	}

	// Upsert alert (Insert or Update if exists)
	// This replaces the check-then-act pattern to avoid race conditions
	if err := h.upsertAlert(ctx, alert); err != nil {
		return "", fmt.Errorf("failed to upsert alert: %w", err)
	}

	// Cache alert in Redis
	if err := h.cacheAlert(ctx, alert); err != nil {
		h.logger.WithError(err).Warn("Failed to cache alert in Redis")
	}

	return alert.ID.String(), nil
}

func (h *AlertHandler) upsertAlert(ctx context.Context, alert *models.Alert) error {
	// Use PostgreSQL ON CONFLICT clause for atomic upsert
	query := `
		INSERT INTO alerts (
			id, external_id, source, severity, title, description,
			labels, annotations, starts_at, ends_at, generator_url,
			fingerprint, status, raw_data, created_at, updated_at
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
		)
		ON CONFLICT (external_id) DO UPDATE SET
			severity = EXCLUDED.severity,
			title = EXCLUDED.title,
			description = EXCLUDED.description,
			labels = EXCLUDED.labels,
			annotations = EXCLUDED.annotations,
			ends_at = EXCLUDED.ends_at,
			generator_url = EXCLUDED.generator_url,
			status = EXCLUDED.status,
			raw_data = EXCLUDED.raw_data,
			updated_at = EXCLUDED.updated_at
		RETURNING id`

	labelsJSON, err := json.Marshal(alert.Labels)
	if err != nil {
		return fmt.Errorf("failed to marshal labels: %w", err)
	}
	
	annotationsJSON, err := json.Marshal(alert.Annotations)
	if err != nil {
		return fmt.Errorf("failed to marshal annotations: %w", err)
	}

	// Execute upsert and get the ID (either new or existing)
	err = h.db.QueryRowContext(ctx, query,
		alert.ID, alert.ExternalID, alert.Source, alert.Severity,
		alert.Title, alert.Description, labelsJSON, annotationsJSON,
		alert.StartsAt, alert.EndsAt, alert.GeneratorURL,
		alert.Fingerprint, alert.Status, alert.RawData,
		alert.CreatedAt, alert.UpdatedAt,
	).Scan(&alert.ID)

	return err
}

func (h *AlertHandler) cacheAlert(ctx context.Context, alert *models.Alert) error {
	key := fmt.Sprintf("alert:%s", alert.ID.String())
	data, err := json.Marshal(alert)
	if err != nil {
		return err
	}

	return h.redis.SetAlert(ctx, key, data, 24*time.Hour)
}

func (h *AlertHandler) extractSeverity(labels map[string]interface{}) string {
	if severity, ok := labels["severity"].(string); ok {
		return severity
	}
	if priority, ok := labels["priority"].(string); ok {
		return priority
	}
	return "medium"
}

func (h *AlertHandler) extractTitle(labels, annotations map[string]interface{}) string {
	if title, ok := annotations["summary"].(string); ok {
		return title
	}
	if title, ok := annotations["title"].(string); ok {
		return title
	}
	if alertname, ok := labels["alertname"].(string); ok {
		return alertname
	}
	return "Unknown Alert"
}

func (h *AlertHandler) extractDescription(annotations map[string]interface{}) string {
	if desc, ok := annotations["description"].(string); ok {
		return desc
	}
	if desc, ok := annotations["message"].(string); ok {
		return desc
	}
	return ""
}

func (h *AlertHandler) GetHealth(c *gin.Context) {
	// Check database health
	if err := h.db.HealthCheck(); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"status": "unhealthy",
			"error":  "database connection failed",
		})
		return
	}

	// Check Redis health
	if err := h.redis.HealthCheck(); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"status": "unhealthy",
			"error":  "redis connection failed",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
		"timestamp": time.Now(),
	})
}