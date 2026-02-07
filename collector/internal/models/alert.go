// Alert data models for KAM Collector service
package models

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
)

type Alert struct {
	ID           uuid.UUID              `json:"id" db:"id"`
	ExternalID   string                 `json:"external_id" db:"external_id"`
	Source       string                 `json:"source" db:"source"`
	Severity     string                 `json:"severity" db:"severity"`
	Title        string                 `json:"title" db:"title"`
	Description  string                 `json:"description" db:"description"`
	Labels       map[string]interface{} `json:"labels" db:"labels"`
	Annotations  map[string]interface{} `json:"annotations" db:"annotations"`
	StartsAt     time.Time              `json:"starts_at" db:"starts_at"`
	EndsAt       *time.Time             `json:"ends_at,omitempty" db:"ends_at"`
	GeneratorURL string                 `json:"generator_url" db:"generator_url"`
	Fingerprint  string                 `json:"fingerprint" db:"fingerprint"`
	Status       string                 `json:"status" db:"status"`
	RawData      json.RawMessage        `json:"raw_data" db:"raw_data"`
	CreatedAt    time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time              `json:"updated_at" db:"updated_at"`
}

type AlertWebhook struct {
	Version           string                 `json:"version"`
	GroupKey          string                 `json:"groupKey"`
	TruncatedAlerts   int                    `json:"truncatedAlerts"`
	Status            string                 `json:"status"`
	Receiver          string                 `json:"receiver"`
	GroupLabels       map[string]interface{} `json:"groupLabels"`
	CommonLabels      map[string]interface{} `json:"commonLabels"`
	CommonAnnotations map[string]interface{} `json:"commonAnnotations"`
	ExternalURL       string                 `json:"externalURL"`
	Alerts            []AlertData            `json:"alerts"`
}

type AlertData struct {
	Status       string                 `json:"status"`
	Labels       map[string]interface{} `json:"labels"`
	Annotations  map[string]interface{} `json:"annotations"`
	StartsAt     time.Time              `json:"startsAt"`
	EndsAt       *time.Time             `json:"endsAt,omitempty"`
	GeneratorURL string                 `json:"generatorURL"`
	Fingerprint  string                 `json:"fingerprint"`
}

type AlertResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	AlertID string `json:"alert_id,omitempty"`
	Error   string `json:"error,omitempty"`
}

func (a *Alert) Validate() error {
	if a.ExternalID == "" {
		return fmt.Errorf("external_id is required")
	}
	if a.Source == "" {
		return fmt.Errorf("source is required")
	}
	if a.Severity == "" {
		return fmt.Errorf("severity is required")
	}
	if a.Title == "" {
		return fmt.Errorf("title is required")
	}
	return nil
}

func (a *Alert) GenerateFingerprint() string {
	// Simple fingerprint generation based on key fields
	data := fmt.Sprintf("%s:%s:%s", a.Source, a.ExternalID, a.Title)
	hash := sha256.Sum256([]byte(data))
	return fmt.Sprintf("%x", hash)
}