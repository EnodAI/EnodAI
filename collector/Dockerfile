# Build Stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Dependency caching için önce mod dosyalarını kopyala
# DÜZELTME: go.sum dosyası sağlanmadığı için COPY komutundan çıkarıldı.
# go mod tidy ile bağımlılıklar çözülüp go.sum oluşturulacak.
COPY go.mod ./
RUN go mod tidy

# Kaynak kodu kopyala ve build et
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o collector .

# Final Stage (Distroless veya Alpine kullanılabilir, Alpine debug için daha iyi)
FROM alpine:3.18

WORKDIR /app

# SSL sertifikaları ve timezone verileri
RUN apk --no-cache add ca-certificates tzdata

COPY --from=builder /app/collector .

# Non-root user güvenliği
RUN adduser -D kamuser
USER kamuser

EXPOSE 8080

CMD ["./collector"]