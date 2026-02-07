package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/jackc/pgx/v4/pgxpool"
)

// Configuration struct
type Config struct {
	DBHost        string
	DBPort        string
	DBName        string
	DBUser        string
	DBPassword    string
	RedisHost     string
	RedisPort     string
	PrometheusURL string
}

// Global clients
var (
	pgPool      *pgxpool.Pool
	redisClient *redis.Client
	cfg         Config
)

func loadConfig() {
	cfg = Config{
		DBHost:        getEnv("DB_HOST", "localhost"),
		DBPort:        getEnv("DB_PORT", "5432"),
		DBName:        getEnv("DB_NAME", "kam_alerts"),
		DBUser:        getEnv("DB_USER", "kam_user"),
		DBPassword:    getEnv("DB_PASSWORD", "kam_password"),
		RedisHost:     getEnv("REDIS_HOST", "localhost"),
		RedisPort:     getEnv("REDIS_PORT", "6379"),
		PrometheusURL: getEnv("PROMETHEUS_URL", "http://localhost:9090"),
	}
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

func initDB() {
	dsn := fmt.Sprintf("postgres://%s:%s@%s:%s/%s", cfg.DBUser, cfg.DBPassword, cfg.DBHost, cfg.DBPort, cfg.DBName)
	var err error
	// Set connection pool config for performance
	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		log.Fatalf("Unable to parse DB config: %v", err)
	}
	config.MaxConns = 25
	config.MinConns = 5
	config.MaxConnLifetime = time.Hour

	pgPool, err = pgxpool.ConnectConfig(context.Background(), config)
	if err != nil {
		log.Fatalf("Unable to connect to database: %v", err)
	}
	log.Println("Connected to PostgreSQL")
}

func initRedis() {
	redisClient = redis.NewClient(&redis.Options{
		Addr:         fmt.Sprintf("%s:%s", cfg.RedisHost, cfg.RedisPort),
		MinIdleConns: 5,
		PoolSize:     20,
	})
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	_, err := redisClient.Ping(ctx).Result()
	if err != nil {
		log.Fatalf("Unable to connect to Redis: %v", err)
	}
	log.Println("Connected to Redis")
}

// Alert structure matching incoming webhook
type Alert struct {
	Status      string            `json:"status"`
	Labels      map[string]string `json:"labels"`
	Annotations map[string]string `json:"annotations"`
	StartsAt    time.Time         `json:"startsAt"`
	EndsAt      time.Time         `json:"endsAt"`
	GeneratorURL string           `json:"generatorURL"`
}

type WebhookMessage struct {
	Receiver string  `json:"receiver"`
	Status   string  `json:"status"`
	Alerts   []Alert `json:"alerts"`
}

func handleWebhook(c *fiber.Ctx) error {
	var msg WebhookMessage
	if err := c.BodyParser(&msg); err != nil {
		return c.Status(400).JSON(fiber.Map{"error": "Invalid JSON format"})
	}

	if len(msg.Alerts) == 0 {
		return c.Status(400).JSON(fiber.Map{"error": "No alerts found in payload"})
	}

	// Use a context with timeout for downstream operations
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	successCount := 0
	for _, alert := range msg.Alerts {
		alertBytes, err := json.Marshal(alert)
		if err != nil {
			log.Printf("Error marshaling alert: %v", err)
			continue
		}

		// 1. Push to Redis Stream for AI processing
		err = redisClient.XAdd(ctx, &redis.XAddArgs{
			Stream: "metrics:raw",
			Values: map[string]interface{}{
				"data":      string(alertBytes),
				"type":      "alert",
				"timestamp": time.Now().Unix(),
			},
		}).Err()

		if err != nil {
			log.Printf("Error pushing to Redis: %v", err)
			// Don't return, try to save to DB at least
		}

		// 2. Persist to PostgreSQL (Cold storage)
		// Use parameterized queries for security (SQL Injection prevention)
		_, err = pgPool.Exec(ctx, `
			INSERT INTO alerts (source, severity, title, description, labels, annotations, starts_at, raw_data, status)
			VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		`, "webhook", alert.Labels["severity"], alert.Annotations["summary"], alert.Annotations["description"],
			alert.Labels, alert.Annotations, alert.StartsAt, alertBytes, alert.Status)

		if err != nil {
			log.Printf("Error saving to DB: %v", err)
		} else {
			successCount++
		}
	}

	return c.JSON(fiber.Map{"status": "received", "processed": successCount, "total": len(msg.Alerts)})
}

// Mock Scraper to simulate Prometheus scraping
func startScraper(done chan bool) {
	ticker := time.NewTicker(15 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-done:
			log.Println("Stopping scraper...")
			return
		case <-ticker.C:
			// In a real scenario, we would query Prometheus API here.
			// For now, we simulate a metric point.
			metric := map[string]interface{}{
				"metric_name":  "cpu_usage",
				"metric_value": 0.45, // Mock value
				"labels":       map[string]string{"host": "server-01"},
				"timestamp":    time.Now(),
			}
			
			metricBytes, _ := json.Marshal(metric)
			
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			
			// Push metric to Redis for Anomaly Detection
			err := redisClient.XAdd(ctx, &redis.XAddArgs{
				Stream: "metrics:raw",
				Values: map[string]interface{}{
					"data":      string(metricBytes),
					"type":      "metric",
					"timestamp": time.Now().Unix(),
				},
			}).Err()
			if err != nil {
				log.Printf("Scraper Redis Error: %v", err)
			}
			
			// Save raw metric to DB for training
			_, err = pgPool.Exec(ctx, `
				INSERT INTO metrics (metric_name, metric_value, labels, timestamp)
				VALUES ($1, $2, $3, $4)
			`, "cpu_usage", 0.45, metric["labels"], time.Now())
			if err != nil {
				log.Printf("Scraper DB Error: %v", err)
			}
			
			cancel()
		}
	}
}

func main() {
	loadConfig()
	initDB()
	initRedis()
	
	// Graceful shutdown handling
	scraperDone := make(chan bool)
	go startScraper(scraperDone)

	app := fiber.New(fiber.Config{
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	})
	app.Use(logger.New())

	app.Post("/api/v1/alerts", handleWebhook)
	app.Get("/health", func(c *fiber.Ctx) error {
		// Basic health check
		if err := pgPool.Ping(context.Background()); err != nil {
			return c.Status(503).SendString("Database Unavailable")
		}
		return c.SendString("OK")
	})

	// Run server in a goroutine
	go func() {
		if err := app.Listen(":8080"); err != nil {
			log.Panicf("Listen failed: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown the server
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	<-c

	log.Println("Gracefully shutting down...")
	
	// Stop scraper
	scraperDone <- true
	
	// Shutdown Fiber
	_ = app.Shutdown()

	// Close connections
	pgPool.Close()
	redisClient.Close()
	
	log.Println("Cleanup finished.")
}