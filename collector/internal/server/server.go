// HTTP server setup for KAM Collector service
package server

import (
	"context"
	"net/http"
	"time"

	"kam-collector/internal/config"
	"kam-collector/internal/handlers"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

type Server struct {
	config       config.ServerConfig
	alertHandler *handlers.AlertHandler
	logger       *logrus.Logger
	httpServer   *http.Server
}

func NewServer(cfg config.ServerConfig, alertHandler *handlers.AlertHandler, logger *logrus.Logger) *Server {
	return &Server{
		config:       cfg,
		alertHandler: alertHandler,
		logger:       logger,
	}
}

func (s *Server) Start() error {
	// Set Gin mode
	gin.SetMode(gin.ReleaseMode)

	// Create Gin router
	router := gin.New()

	// Add middleware
	router.Use(gin.Recovery())
	router.Use(s.loggingMiddleware())
	router.Use(s.corsMiddleware())

	// Setup routes
	s.setupRoutes(router)

	// Create HTTP server
	s.httpServer = &http.Server{
		Addr:         ":" + s.config.Port,
		Handler:      router,
		ReadTimeout:  time.Duration(s.config.ReadTimeout) * time.Second,
		WriteTimeout: time.Duration(s.config.WriteTimeout) * time.Second,
	}

	return s.httpServer.ListenAndServe()
}

func (s *Server) Shutdown(ctx context.Context) error {
	if s.httpServer != nil {
		return s.httpServer.Shutdown(ctx)
	}
	return nil
}

func (s *Server) setupRoutes(router *gin.Engine) {
	// Health check endpoint
	router.GET("/health", s.alertHandler.GetHealth)

	// API v1 routes
	v1 := router.Group("/api/v1")
	{
		// Alert webhook endpoint
		v1.POST("/alerts/webhook", s.alertHandler.HandleWebhook)
	}

	// Root endpoint
	router.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"service": "KAM Collector",
			"version": "1.0.0",
			"status":  "running",
		})
	})
}

func (s *Server) loggingMiddleware() gin.HandlerFunc {
	return gin.LoggerWithFormatter(func(param gin.LogFormatterParams) string {
		s.logger.WithFields(logrus.Fields{
			"status_code": param.StatusCode,
			"latency":     param.Latency,
			"client_ip":   param.ClientIP,
			"method":      param.Method,
			"path":        param.Path,
			"user_agent":  param.Request.UserAgent(),
		}).Info("HTTP Request")
		return ""
	})
}

func (s *Server) corsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		c.Next()
	}
}