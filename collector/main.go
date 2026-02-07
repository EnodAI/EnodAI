package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/redis/go-redis/v9"
)

// Global Variables
var (
	dbPool      *pgxpool.Pool
	redisClient *redis.Client
	
	// Prometheus Metrics
	alertsReceived = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "enod_alerts_received_total",
		Help: "Total number of alerts received",
	})
	metricsReceived = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "enod_metrics_received_total",
		Help: "Total number of metrics received",
	})
	processingDuration = prometheus.NewHistogram(prometheus.HistogramOpts{
		Name:    "enod_processing_duration_seconds",
		Help:    "Time taken to process requests",
		Buckets: prometheus.DefBuckets,
	})
)

// Data Structures
type MetricPayload struct {
	MetricName  string                 `json:"metric_name" binding:"required"`
	MetricValue float64                `json:"metric_value" binding:"required"`
	Labels      map[string]interface{} `json:"labels"`
}

type AlertPayload struct {
	Labels       map[string]string `json:"labels" binding:"required"`
	Annotations  map[string]string `json:"annotations"`
	StartsAt     time.Time         `json:"startsAt"`
	EndsAt       time.Time         `json:"endsAt"`
	GeneratorURL string            `json:"generatorURL"`
}

func init() {
	// Register metrics
	prometheus.MustRegister(alertsReceived)
	prometheus.MustRegister(metricsReceived)
	prometheus.MustRegister(processingDuration)
}

func main() {
	// 1. Configuration & Connection Setup
	dbHost := os.Getenv("DB_HOST")
	dbUser := os.Getenv("DB_USER")
	dbPass := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")
	redisAddr := os.Getenv("REDIS_ADDR")

	// Database Connection (Pool for Performance)
	dbURL := fmt.Sprintf("postgres://%s:%s@%s:5432/%s", dbUser, dbPass, dbHost, dbName)
	config, err := pgxpool.ParseConfig(dbURL)
	if err != nil {
		log.Fatalf("Unable to parse database config: %v", err)
	}
	// Connection pool settings
	config.MaxConns = 25
	config.MinConns = 5
	config.MaxConnLifetime = time.Hour

	ctx := context.Background()
	dbPool, err = pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		log.Fatalf("Unable to create connection pool: %v", err)
	}
	defer dbPool.Close()

	// Redis Connection
	redisClient = redis.NewClient(&redis.Options{
		Addr:         redisAddr,
		Password:     "",
		DB:           0,
		ReadTimeout:  3 * time.Second,
		WriteTimeout: 3 * time.Second,
		PoolSize:     20,
	})

	// Verify connections
	if err := dbPool.Ping(ctx); err != nil {
		log.Fatalf("Database connection failed: %v", err)
	}
	if err := redisClient.Ping(ctx).Err(); err != nil {
		log.Fatalf("Redis connection failed: %v", err)
	}

	log.Println("Connected to PostgreSQL and Redis successfully.")

	// 2. Gin Router Setup
	r := gin.Default() // Default includes logger and recovery middleware

	// Security: Trusted Proxies (In Docker, we trust the internal network or specific gateway)
	// For simplicity in this setup, we trust all (be careful in prod)
	r.SetTrustedProxies(nil)

	// Routes
	r.GET("/health", healthCheck)
	r.GET("/metrics", gin.WrapH(promhttp.Handler()))
	
	api := r.Group("/api/v1")
	{
		api.POST("/alerts", handleAlerts)
		api.POST("/metrics", handleMetrics)
	}

	// Start Server
	log.Println("Collector service starting on :8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

// Handlers

func healthCheck(c *gin.Context) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	dbStatus := "up"
	if err := dbPool.Ping(ctx); err != nil {
		dbStatus = "down"
	}

	redisStatus := "up"
	if err := redisClient.Ping(ctx).Err(); err != nil {
		redisStatus = "down"
	}

	if dbStatus == "down" || redisStatus == "down" {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"status": "unhealthy",
			"db":     dbStatus,
			"redis":  redisStatus,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "healthy"})
}

func handleMetrics(c *gin.Context) {
	timer := prometheus.NewTimer(processingDuration)
	defer timer.ObserveDuration()

	var payload MetricPayload
	// Input Validation
	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// 1. Store in DB (SQL Injection safe via pgx arguments)
	// Using JSONB for labels
	_, err := dbPool.Exec(ctx, 
		"INSERT INTO metrics (metric_name, metric_value, labels) VALUES ($1, $2, $3)",
		payload.MetricName, payload.MetricValue, payload.Labels)
	
	if err != nil {
		log.Printf("Error saving metric to DB: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}

	// 2. Publish to Redis Stream (Async for AI processing)
	// Non-blocking approach for HTTP response, but we wait here for data integrity
	streamData, _ := json.Marshal(payload)
	err = redisClient.XAdd(ctx, &redis.XAddArgs{
		Stream: "metrics:raw",
		Values: map[string]interface{}{
			"type": "metric",
			"data": string(streamData),
			"ts":   time.Now().Unix(),
		},
		// Limit stream size to prevent memory overflow if consumer is slow
		MaxLenApprox: 10000, 
	}).Err()

	if err != nil {
		log.Printf("Error publishing to Redis: %v", err)
		// We don't fail the request if Redis fails, but log it. 
		// Depending on requirement, might return 202 Accepted with warning.
	}

	metricsReceived.Inc()
	c.JSON(http.StatusCreated, gin.H{"status": "processed"})
}

func handleAlerts(c *gin.Context) {
	timer := prometheus.NewTimer(processingDuration)
	defer timer.ObserveDuration()

	var alerts []AlertPayload
	// Prometheus AlertManager sends an array of alerts
	if err := c.ShouldBindJSON(&alerts); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	for _, alert := range alerts {
		// 1. Store in DB
		alertName := alert.Labels["alertname"]
		severity := alert.Labels["severity"]
		description := alert.Annotations["description"]

		var alertID int
		err := dbPool.QueryRow(ctx, `
			INSERT INTO alerts (alert_name, severity, description, labels, annotations, starts_at, ends_at, generator_url)
			VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
			RETURNING id
		`, alertName, severity, description, alert.Labels, alert.Annotations, alert.StartsAt, alert.EndsAt, alert.GeneratorURL).Scan(&alertID)

		if err != nil {
			log.Printf("Error saving alert to DB: %v", err)
			continue // Try next alert
		}

		// 2. Publish to Redis Stream for AI Analysis
		streamData, _ := json.Marshal(map[string]interface{}{
			"alert_id": alertID,
			"payload":  alert,
		})

		err = redisClient.XAdd(ctx, &redis.XAddArgs{
			Stream: "metrics:raw", // Using same stream for simplicity or split to "alerts:raw"
			Values: map[string]interface{}{
				"type": "alert",
				"data": string(streamData),
				"ts":   time.Now().Unix(),
			},
		}).Err()

		if err != nil {
			log.Printf("Error publishing alert to Redis: %v", err)
		}
	}

	alertsReceived.Add(float64(len(alerts)))
	c.JSON(http.StatusOK, gin.H{"status": "processed", "count": len(alerts)})
}