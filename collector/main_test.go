package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func setupTestRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.Default()
	r.SetTrustedProxies(nil)

	r.GET("/health", healthCheck)

	api := r.Group("/api/v1")
	{
		api.POST("/metrics", handleMetrics)
		api.POST("/alerts", handleAlerts)
	}

	return r
}

func TestHealthCheck(t *testing.T) {
	router := setupTestRouter()

	req, _ := http.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "healthy", response["status"])
}

func TestHandleMetrics_ValidPayload(t *testing.T) {
	router := setupTestRouter()

	payload := MetricPayload{
		MetricName:  "cpu_usage",
		MetricValue: 75.5,
		Labels: map[string]interface{}{
			"host": "test-server",
		},
	}

	jsonData, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", "/api/v1/metrics", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "processed", response["status"])
}

func TestHandleMetrics_InvalidPayload(t *testing.T) {
	router := setupTestRouter()

	invalidPayload := map[string]interface{}{
		"metric_name": "cpu_usage",
		// Missing metric_value
	}

	jsonData, _ := json.Marshal(invalidPayload)
	req, _ := http.NewRequest("POST", "/api/v1/metrics", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestHandleMetrics_MalformedJSON(t *testing.T) {
	router := setupTestRouter()

	req, _ := http.NewRequest("POST", "/api/v1/metrics", bytes.NewBufferString("{invalid json}"))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestHandleAlerts_ValidPayload(t *testing.T) {
	router := setupTestRouter()

	alerts := []AlertPayload{
		{
			Labels: map[string]string{
				"alertname": "HighCPU",
				"severity":  "critical",
			},
			Annotations: map[string]string{
				"description": "CPU usage above 90%",
			},
		},
	}

	jsonData, _ := json.Marshal(alerts)
	req, _ := http.NewRequest("POST", "/api/v1/alerts", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "processed", response["status"])
	assert.Equal(t, float64(1), response["count"])
}

func TestHandleAlerts_EmptyArray(t *testing.T) {
	router := setupTestRouter()

	alerts := []AlertPayload{}

	jsonData, _ := json.Marshal(alerts)
	req, _ := http.NewRequest("POST", "/api/v1/alerts", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, float64(0), response["count"])
}

func TestHandleAlerts_InvalidPayload(t *testing.T) {
	router := setupTestRouter()

	req, _ := http.NewRequest("POST", "/api/v1/alerts", bytes.NewBufferString("invalid"))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func BenchmarkHandleMetrics(b *testing.B) {
	router := setupTestRouter()

	payload := MetricPayload{
		MetricName:  "cpu_usage",
		MetricValue: 75.5,
		Labels: map[string]interface{}{
			"host": "test-server",
		},
	}

	jsonData, _ := json.Marshal(payload)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req, _ := http.NewRequest("POST", "/api/v1/metrics", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)
	}
}

func BenchmarkHandleAlerts(b *testing.B) {
	router := setupTestRouter()

	alerts := []AlertPayload{
		{
			Labels: map[string]string{
				"alertname": "HighCPU",
				"severity":  "critical",
			},
			Annotations: map[string]string{
				"description": "CPU usage above 90%",
			},
		},
	}

	jsonData, _ := json.Marshal(alerts)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req, _ := http.NewRequest("POST", "/api/v1/alerts", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)
	}
}
