# Book Management API v14

Book Management System with webhook notifications, structured logging, and Prometheus metrics.

## Quick Start

```powershell
# Install
pip install -r requirements.txt

# Run
python -m book_management_flask_v14.run

# Access
http://localhost:5000        # Developer Portal
http://localhost:5000/app    # Web Application
http://localhost:5000/swagger # API Documentation
```

## Features

- RESTful API with JWT authentication
- Webhook notifications (book_borrowed, book_returned, user_registered)
- Structured logging (JSON format)
- Prometheus metrics integration
- API versioning (v1 deprecated, v2 current)
- In-memory caching with TTL
- OAuth2/OIDC support (Google)

## API Endpoints

### Authentication
```
POST   /api/auth/register     # Register user
POST   /api/auth/login        # Login (get JWT token)
POST   /api/auth/logout       # Logout
GET    /api/auth/me           # Get current user
```

### Books
```
GET    /api/book_titles       # List book titles
POST   /api/book_titles       # Create book title
GET    /api/v2/book-copies    # List book copies (v2)
POST   /api/v2/book-copies    # Create book copy
```

### Borrowings
```
GET    /api/borrowings        # List borrowings
POST   /api/borrowings        # Borrow book
POST   /api/borrowings/{id}/return  # Return book
```

### Monitoring
```
GET    /health                # Health check
GET    /metrics               # Prometheus metrics
```

### Webhooks
```
GET    /webhooks              # List webhook URLs
POST   /webhooks              # Add webhook URL
DELETE /webhooks/{url}        # Remove webhook
POST   /webhooks/test         # Test webhook
```

## Usage Examples

### Register and Login
```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com"}'
```

### Create Book and Borrow
```bash
# Create book title
curl -X POST http://localhost:5000/api/book_titles \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Clean Code", "author": "Robert Martin"}'

# Create book copy
curl -X POST http://localhost:5000/api/v2/book-copies \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"book_title_id": 1, "barcode": "BC001"}'

# Borrow book
curl -X POST http://localhost:5000/api/borrowings \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"book_copy_id": 1, "due_date": "2025-12-31T23:59:59"}'
```

### Configure Webhooks
```bash
# Add webhook
curl -X POST http://localhost:5000/webhooks \
  -H "Content-Type: application/json" \
  -d '{"url": "https://webhook.site/your-id"}'

# Test webhook
curl -X POST http://localhost:5000/webhooks/test
```

## Webhook Events

All webhooks receive JSON payloads:

```json
{
  "timestamp": "2025-12-04T10:30:00Z",
  "event_type": "book_borrowed",
  "service": "book_management_api",
  "version": "v14",
  "data": {
    "borrowing_id": 123,
    "user_id": 45,
    "book_title": "Clean Code",
    "due_date": "2025-12-18T10:30:00"
  }
}
```

Events: `book_borrowed`, `book_returned`, `user_registered`, `system_health`

## Configuration

Environment variables:

```powershell
$env:SECRET_KEY="your-secret-key"
$env:LOG_LEVEL="INFO"
$env:WEBHOOK_URLS="https://webhook.site/abc,https://hooks.slack.com/xyz"
$env:GOOGLE_CLIENT_ID="your-client-id"
$env:GOOGLE_CLIENT_SECRET="your-client-secret"
```

## Monitoring

### Logs
```
logs/book_management.log        # All logs (JSON)
logs/book_management_error.log  # Errors only
```

### Metrics
```bash
curl http://localhost:5000/metrics
```

Key metrics:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Response time
- `cache_hits_total` / `cache_misses_total` - Cache performance
- `books_borrowed_total` / `books_returned_total` - Business metrics
- `active_borrowings_total` - Current borrowings

### Grafana Queries
```
rate(http_requests_total[5m])
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

## Testing

```powershell
# Run tests
pytest tests/

# Demo scripts
python demo_monitoring.py
python demo_webhook.py
```

## API Versioning

- v1: Deprecated (sunset: 2026-06-01)
- v2: Current (use `/api/v2/book-copies`)

v2 improvements:
- Embedded book title information
- Advanced filtering (`?available=true&condition=Good`)
- PATCH support for partial updates
- Structured error responses

## Troubleshooting

### Common Issues

**ModuleNotFoundError:**
```bash
pip install -r requirements.txt
```

**Token invalid:**
```bash
# Login again to get new token
curl -X POST http://localhost:5000/api/auth/login -d '{"email": "user@example.com"}'
```

**Webhook not sending:**
```bash
# Check configuration
curl http://localhost:5000/webhooks

# Check logs
cat logs/book_management.log | grep webhook
```

## Resources

- Developer Portal: http://localhost:5000
- API Documentation: http://localhost:5000/swagger
- OpenAPI Spec: http://localhost:5000/openapi.yaml
- Health Check: http://localhost:5000/health
- Metrics: http://localhost:5000/metrics

## Project Structure

```
book_management_flask_v14/
├── api.py                # API endpoints
├── models.py             # Database models
├── webhook.py            # Webhook system
├── logging_config.py     # Logging setup
├── metrics.py            # Prometheus metrics
├── templates/            # HTML templates
│   └── portal.html       # Developer portal
├── static/               # CSS, JS files
├── tests/                # Test suite
└── requirements.txt      # Dependencies
```

## Version History

- v14: Webhook notifications
- v13: Logging & monitoring
- v12: API versioning
- v11: OpenAPI/Swagger
- v10: JWT authentication

---

Updated: December 4, 2025  
Version: 14.0.0  
Repository: https://github.com/nmhung1294/INT3505E_02_demo
