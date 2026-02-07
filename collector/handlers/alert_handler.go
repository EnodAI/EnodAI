package handlers

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"time"

	"sensusai/collector/database"
	"sensusai/collector/models"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

func HealthCheck(c *gin.Context) {
	// Deep health check
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	if err := database.DB.Ping(ctx); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"status": "error", "component": "database", "message": err.Error()})
		return
	}

	if err := database.Redis.Ping(ctx).Err(); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"status": "error", "component": "redis", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func ReceiveAlerts(c *gin.Context) {
	var payload models.AlertPayload

	// Input Validation
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if len(payload.Alerts) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "empty alert list"})
		return
	}

	var alertIDs []string
	ctx := context.Background()

	// Transaction for atomic operations
	tx, err := database.DB.Begin(ctx)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to start transaction"})
		return
	}
	defer tx.Rollback(ctx)

	for _, alert := range payload.Alerts {
		id := uuid.New()
		
		// Safe JSON marshaling
		labelsJSON, _ := json.Marshal(alert.Labels)
		annotationsJSON, _ := json.Marshal(alert.Annotations)

		// SQL Injection Safe Query
		query := `
			INSERT INTO alerts (id, title, severity, labels, annotations, starts_at, ends_at, status)
			VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		`
		
		severity := alert.Labels["severity"]
		if severity == "" {
			severity = "unknown"
		}
		
		title := alert.Annotations["summary"]
		if title == "" {
			title = alert.Labels["alertname"]
		}

		_, err := tx.Exec(ctx, query,
			id,
			title,
			severity,
			labelsJSON,
			annotationsJSON,
			alert.StartsAt,
			alert.EndsAt,
			"firing",
		)

		if err != nil {
			log.Printf("Error inserting alert: %v", err)
			continue // Skip failed alert, try others
		}

		// Prepare for Redis Stream
		streamMsg := map[string]interface{}{
			"id":        id.String(),
			"alertname": alert.Labels["alertname"],
			"severity":  severity,
			"labels":    string(labelsJSON),
			"timestamp": time.Now().Format(time.RFC3339),
		}
		
		msgBytes, _ := json.Marshal(streamMsg)

		// Publish to Redis Stream
		err = database.Redis.XAdd(ctx, &redis.XAddArgs{
			Stream: "metrics:raw",
			Values: map[string]interface{}{
				"type": "alert",
				"data": string(msgBytes),
			},
		}).Err()

		if err != nil {
			log.Printf("Error publishing to redis: %v", err)
			// Note: We don't rollback DB transaction here to ensure data persistence even if stream fails
		}

		alertIDs = append(alertIDs, id.String())
	}

	if err := tx.Commit(ctx); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to commit transaction"})
		return
	}

	c.JSON(http.StatusCreated, models.AlertResponse{
		Status:    "success",
		Processed: len(alertIDs),
		AlertIDs:  alertIDs,
	})
}