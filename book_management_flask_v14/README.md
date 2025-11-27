# Book Management System - Version 14

## Tổng quan

Version 14 là phiên bản mới nhất của hệ thống quản lý thư viện, bổ sung tính năng **Webhook Notifications** vào hệ thống logging và monitoring hiện có.

### Tính năng chính

**Version 14 - Webhook Notifications**
- Webhook notifications cho các sự kiện quan trọng
- Gửi thông báo bất đồng bộ (non-blocking)
- Quản lý webhook URLs qua REST API
- Timeout protection và error handling
- Hỗ trợ multiple webhook endpoints

**Version 13 - Logging & Monitoring**
- Structured logging với JSON format
- Prometheus metrics integration
- Health check endpoint
- Request tracking và performance monitoring
- Business metrics (borrowings, registrations, auth)

**Version 12 và trước**
- API versioning (v1 deprecated, v2 current)
- JWT authentication với HTTP-only cookies
- OAuth2/OIDC integration (Google)
- RESTful API với caching
- SQLite database với SQLAlchemy ORM

## Cài đặt nhanh

### Yêu cầu
- Python 3.8+
- pip

### Các bước cài đặt

```powershell
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Cấu hình webhook URLs (tùy chọn)
$env:WEBHOOK_URLS="https://webhook.site/your-unique-id"

# 3. Chạy ứng dụng
python -m book_management_flask_v14.run

# Server chạy tại: http://localhost:5000
```

### Kiểm tra hoạt động

```powershell
# Health check
curl http://localhost:5000/health

# Metrics endpoint
curl http://localhost:5000/metrics

# Xem webhooks đã cấu hình
curl http://localhost:5000/webhooks

# Swagger UI
# Truy cập: http://localhost:5000/swagger
```

## Cấu trúc dự án

```
book_management_flask_v14/
├── api.py                    # API endpoints và business logic
├── models.py                 # Database models (SQLAlchemy)
├── run.py                    # Application entry point
├── __init__.py              # Flask app initialization
│
├── logging_config.py         # Logging configuration
├── metrics.py                # Prometheus metrics
├── webhook.py                # Webhook notification system
│
├── templates/                # HTML templates
├── static/                   # Static files (CSS, JS)
├── tests/                    # Test suite
├── examples/                 # Code examples
├── logs/                     # Log files
│
├── requirements.txt          # Python dependencies
├── openapi.yaml             # OpenAPI specification
├── prometheus.yml           # Prometheus config
└── prometheus_alerts.yml    # Alert rules
```

## API Endpoints

### Authentication

```
POST   /api/auth/register          # Đăng ký user mới
POST   /api/auth/login             # Đăng nhập (JWT token)
POST   /api/auth/logout            # Đăng xuất
GET    /api/auth/me                # Thông tin user hiện tại
```

### Book Titles

```
GET    /api/book_titles            # Danh sách book titles
GET    /api/book_titles/{id}       # Chi tiết book title
POST   /api/book_titles            # Tạo book title mới
PUT    /api/book_titles/{id}       # Cập nhật book title
DELETE /api/book_titles/{id}       # Xóa book title
```

### Book Copies (Version 1 - Deprecated)

```
GET    /api/book_copies            # Danh sách book copies
POST   /api/book_copies            # Tạo book copy
PUT    /api/book_copies/{id}       # Cập nhật book copy
DELETE /api/book_copies/{id}       # Xóa book copy
```

Lưu ý: API v1 đã deprecated, sẽ sunset vào 01/06/2026.

### Book Copies (Version 2 - Current)

```
GET    /api/v2/book-copies                    # Danh sách book copies
GET    /api/v2/book-copies/{id}               # Chi tiết book copy
POST   /api/v2/book-copies                    # Tạo book copy
PUT    /api/v2/book-copies/{id}               # Cập nhật hoàn toàn
PATCH  /api/v2/book-copies/{id}               # Cập nhật một phần
DELETE /api/v2/book-copies/{id}               # Xóa book copy
GET    /api/v2/book-copies?available=true     # Lọc theo available
GET    /api/v2/book-copies?condition=Good     # Lọc theo condition
GET    /api/v2/book-copies?search=BC001       # Tìm kiếm theo barcode
```

### Users

```
GET    /api/users                  # Danh sách users
GET    /api/users/{id}             # Chi tiết user
POST   /api/users                  # Tạo user mới
PUT    /api/users/{id}             # Cập nhật user
DELETE /api/users/{id}             # Xóa user
```

### Borrowings

```
GET    /api/borrowings             # Danh sách borrowings
GET    /api/borrowings/{id}        # Chi tiết borrowing
POST   /api/borrowings             # Mượn sách
POST   /api/borrowings/{id}/return # Trả sách
```

### Monitoring & Health

```
GET    /health                     # Health check
GET    /metrics                    # Prometheus metrics
```

### Webhook Management

```
GET    /webhooks                   # Danh sách webhook URLs
POST   /webhooks                   # Thêm webhook URL
DELETE /webhooks/{url}             # Xóa webhook URL
POST   /webhooks/test              # Gửi test notification
```

## Webhook Notifications

### Cấu hình Webhooks

Via Environment Variable:
```powershell
$env:WEBHOOK_URLS="https://webhook.site/abc123,https://hooks.slack.com/services/xxx"
```

Via REST API:
```powershell
# Thêm webhook
curl -X POST http://localhost:5000/webhooks `
  -H "Content-Type: application/json" `
  -d '{"url": "https://webhook.site/test"}'

# Xem webhooks
curl http://localhost:5000/webhooks

# Test webhook
curl -X POST http://localhost:5000/webhooks/test

# Xóa webhook
curl -X DELETE http://localhost:5000/webhooks/https://webhook.site/test
```

### Các sự kiện Webhook

**1. book_borrowed** - Khi user mượn sách
```json
{
  "timestamp": "2025-11-27T10:30:00Z",
  "event_type": "book_borrowed",
  "service": "book_management_api",
  "version": "v14",
  "data": {
    "borrowing_id": 123,
    "user_id": 45,
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "book_copy_id": 789,
    "book_title": "Clean Code",
    "book_author": "Robert Martin",
    "borrow_date": "2025-11-27T10:30:00",
    "due_date": "2025-12-11T10:30:00"
  }
}
```

**2. book_returned** - Khi user trả sách
```json
{
  "timestamp": "2025-11-27T14:30:00Z",
  "event_type": "book_returned",
  "service": "book_management_api",
  "version": "v14",
  "data": {
    "borrowing_id": 123,
    "user_id": 45,
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "book_copy_id": 789,
    "book_title": "Clean Code",
    "book_author": "Robert Martin",
    "borrow_date": "2025-11-27T10:30:00",
    "return_date": "2025-11-27T14:30:00",
    "due_date": "2025-12-11T10:30:00",
    "fine": 0.0,
    "overdue_days": 0
  }
}
```

**3. user_registered** - Khi user mới đăng ký
```json
{
  "timestamp": "2025-11-27T09:00:00Z",
  "event_type": "user_registered",
  "service": "book_management_api",
  "version": "v14",
  "data": {
    "user_id": 45,
    "user_name": "John Doe",
    "user_email": "john@example.com"
  }
}
```

**4. system_health** - Test notifications
```json
{
  "timestamp": "2025-11-27T12:00:00Z",
  "event_type": "system_health",
  "service": "book_management_api",
  "version": "v14",
  "data": {
    "message": "Test webhook notification",
    "timestamp": "2025-11-27T12:00:00Z"
  }
}
```

### Tích hợp Webhook

Slack:
```
URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Discord:
```
URL: https://discord.com/api/webhooks/YOUR/WEBHOOK
```

Webhook.site (Testing):
```
URL: https://webhook.site
```
1. Truy cập https://webhook.site
2. Copy URL được tạo
3. Thêm vào ứng dụng qua API
4. Xem payload real-time

### Đặc điểm Webhook

- Gửi bất đồng bộ (không blocking API response)
- Timeout: 5 giây
- Retry: Không tự động retry (log error)
- Error handling: Tiếp tục hoạt động khi webhook fail
- Logging: Chi tiết trong logs/book_management.log

## Logging & Monitoring

### Structured Logging

Log Levels:
- DEBUG: Chi tiết operations (cache hits/misses, db queries)
- INFO: Normal operations (requests, auth)
- WARNING: Potential issues (failed auth, unavailable books)
- ERROR: Operation failures
- CRITICAL: System failures

Log Files:
```
logs/book_management.log        # Tất cả logs (JSON format)
logs/book_management_error.log  # Chỉ errors (JSON format)
```

Log Format (JSON):
```json
{
  "timestamp": "2025-11-27T10:15:30Z",
  "level": "INFO",
  "logger": "book_management",
  "message": "User logged in",
  "module": "api",
  "function": "login",
  "line": 235,
  "user_id": 1,
  "endpoint": "api.login"
}
```

### Prometheus Metrics

HTTP Metrics:
- http_requests_total: Tổng số requests
- http_request_duration_seconds: Response time histogram
- http_errors_total: Tổng số errors
- http_requests_active: Số requests đang xử lý

Database Metrics:
- db_operations_total: Tổng số DB operations
- db_operation_duration_seconds: DB operation duration
- db_errors_total: Tổng số DB errors

Cache Metrics:
- cache_hits_total: Cache hits
- cache_misses_total: Cache misses
- cache_size_bytes: Cache size
- cache_entries_total: Số entries trong cache

Business Metrics:
- books_borrowed_total: Tổng số sách được mượn
- books_returned_total: Tổng số sách được trả
- active_borrowings_total: Số borrowings đang active
- user_registrations_total: Tổng số đăng ký user
- auth_attempts_total: Tổng số authentication attempts

Xem Metrics:
```powershell
curl http://localhost:5000/metrics
```

### Grafana Dashboard

Cài đặt Prometheus:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'book_management'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:5000']
```

Queries mẫu:
```
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_errors_total[5m])

# Response time p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# Active borrowings
active_borrowings_total
```

## Authentication

### JWT Authentication

Login:
```powershell
curl -X POST http://localhost:5000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email": "user@example.com"}'
```

Response:
- Token được lưu trong HTTP-only cookie `auth_token`
- Hoặc trả về trong response body

Sử dụng token:
```powershell
# Với cookie (tự động)
curl http://localhost:5000/api/book_titles

# Với Authorization header
curl http://localhost:5000/api/book_titles `
  -H "Authorization: Bearer YOUR_TOKEN"
```

### OAuth2/OIDC (Google)

Cấu hình:
```powershell
$env:GOOGLE_CLIENT_ID="your-client-id"
$env:GOOGLE_CLIENT_SECRET="your-client-secret"
$env:GOOGLE_OAUTH_REDIRECT_URI="http://localhost:5000/api/auth/google/callback"
```

Endpoints:
```
GET  /api/auth/google/login      # Redirect to Google login
GET  /api/auth/google/callback   # OAuth callback
```

## Caching

Hệ thống sử dụng in-memory cache với TTL 60 giây.

Cached Endpoints:
- GET /api/book_titles
- GET /api/book_copies
- GET /api/users

Cache Invalidation:
- Tự động xóa khi có thay đổi (POST, PUT, DELETE)
- Cache prefix-based deletion

## Testing

### Chạy Tests

```powershell
# Tất cả tests
pytest tests/

# Specific test file
pytest tests/test_api_versioning.py

# Với coverage
pytest --cov=book_management_flask_v14 tests/
```

### Demo Scripts

Demo Monitoring & Webhook:
```powershell
python demo_monitoring.py
```
- Tạo user, mượn/trả sách
- Hiển thị metrics
- Test webhook notifications

Demo Webhook riêng:
```powershell
python demo_webhook.py
```
- Quản lý webhook URLs
- Trigger các sự kiện webhook
- Xem payload examples

## Cấu hình

### Environment Variables

```powershell
# Authentication
$env:SECRET_KEY="your-secret-key"
$env:AUTH_MODE="jwt"  # hoặc "oauth2"

# OAuth2
$env:GOOGLE_CLIENT_ID="your-client-id"
$env:GOOGLE_CLIENT_SECRET="your-client-secret"
$env:GOOGLE_OAUTH_REDIRECT_URI="http://localhost:5000/api/auth/google/callback"

# OAuth2 Introspection
$env:OAUTH2_INTROSPECTION_URL="https://your-oauth-server/introspect"
$env:OAUTH2_INTROSPECTION_CLIENT_ID="client-id"
$env:OAUTH2_INTROSPECTION_CLIENT_SECRET="client-secret"

# Logging
$env:LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
$env:ENVIRONMENT="development"  # hoặc "production"

# Webhooks
$env:WEBHOOK_URLS="https://webhook.site/abc,https://hooks.slack.com/xxx"

# Business Rules
$env:LIBRARY_FINE_PER_DAY="5000"  # VND per day
```

### File cấu hình

.env file:
```
SECRET_KEY=your-secret-key
AUTH_MODE=jwt
LOG_LEVEL=INFO
ENVIRONMENT=development
WEBHOOK_URLS=https://webhook.site/your-id
```

## API Versioning

### Version 1 (Deprecated)

- Status: Deprecated từ 13/11/2025
- Sunset date: 01/06/2026
- Migration: Chuyển sang v2

Deprecation Headers:
```
Deprecation: true
Sunset: 2026-06-01
Link: </api/v2/book-copies>; rel="successor-version"
Warning: 299 - "This API version is deprecated. Please migrate to v2"
```

### Version 2 (Current)

Improvements:
- Embedded book title information (giảm API calls)
- Advanced filtering (available, condition, search)
- PATCH support (partial updates)
- Real-time borrowing status
- Structured error responses với error codes

Migration Guide:

v1:
```json
GET /api/book_copies/1
{
  "id": 1,
  "book_title_id": 5,
  "barcode": "BC001",
  "available": true,
  "condition": "Good"
}
```

v2:
```json
GET /api/v2/book-copies/1
{
  "id": 1,
  "barcode": "BC001",
  "available": true,
  "condition": "Good",
  "bookTitle": {
    "id": 5,
    "title": "Clean Code",
    "author": "Robert Martin",
    "publisher": "Prentice Hall",
    "year": 2008,
    "category": "Programming"
  },
  "currentBorrowing": null
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "BOOK_NOT_AVAILABLE",
    "message": "This book copy is currently not available",
    "details": {
      "bookCopyId": 123,
      "currentBorrowing": {
        "id": 456,
        "userId": 789,
        "dueDate": "2025-12-15"
      }
    }
  }
}
```

### Error Codes

- BOOK_NOT_AVAILABLE: Sách không khả dụng
- ALREADY_RETURNED: Sách đã được trả
- INVALID_CREDENTIALS: Thông tin đăng nhập sai
- RESOURCE_NOT_FOUND: Không tìm thấy resource
- VALIDATION_ERROR: Dữ liệu không hợp lệ
- UNAUTHORIZED: Chưa xác thực
- FORBIDDEN: Không có quyền truy cập

## Security

### Best Practices

1. JWT Token:
   - Sử dụng HTTP-only cookies
   - Token expiration: 24 giờ
   - Refresh token khi cần

2. Password:
   - Không lưu plain text password
   - Sử dụng bcrypt/scrypt để hash

3. HTTPS:
   - Sử dụng HTTPS trong production
   - Secure cookies với `secure=True`

4. CORS:
   - Cấu hình CORS cho production
   - Chỉ cho phép trusted origins

5. Rate Limiting:
   - Implement rate limiting cho API
   - Protect against brute force attacks

6. Input Validation:
   - Validate tất cả input
   - Sanitize user data

## Troubleshooting

### Lỗi thường gặp

1. ModuleNotFoundError:
```
Lỗi: ModuleNotFoundError: No module named 'flask'
Giải pháp: pip install -r requirements.txt
```

2. Database not found:
```
Lỗi: OperationalError: no such table
Giải pháp: Database được tạo tự động khi chạy lần đầu
```

3. Token invalid:
```
Lỗi: {"message": "Invalid token"}
Giải pháp: Login lại để lấy token mới
```

4. Webhook not sending:
```
Kiểm tra:
- curl http://localhost:5000/webhooks (xem webhooks configured)
- cat logs/book_management.log | grep webhook (xem logs)
- Verify webhook URL is accessible
```

5. Metrics endpoint empty:
```
Kiểm tra:
- prometheus-client đã install chưa
- Server đã khởi động hoàn toàn chưa
```

### Debug Mode

```powershell
# Bật debug mode
$env:FLASK_DEBUG="1"
python -m book_management_flask_v14.run
```

### Xem Logs

```powershell
# Tất cả logs
cat logs/book_management.log

# Chỉ errors
cat logs/book_management_error.log

# Filter by keyword
cat logs/book_management.log | grep "webhook"
cat logs/book_management.log | grep "ERROR"
```

## Performance

### Caching Strategy

- Cache TTL: 60 giây
- Cache invalidation: Prefix-based
- Cache storage: In-memory (Redis trong production)

### Database Optimization

- Index trên foreign keys
- Eager loading cho relationships
- Query optimization với SQLAlchemy

### Monitoring Performance

```
# Response time p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Slow queries (>100ms)
db_operation_duration_seconds_bucket{le="0.1"}
```

## Deployment

### Production Checklist

- Set SECRET_KEY
- Set LOG_LEVEL=WARNING hoặc ERROR
- Set ENVIRONMENT=production
- Cấu hình HTTPS
- Setup Prometheus + Grafana
- Configure webhooks cho monitoring
- Enable secure cookies
- Setup rate limiting
- Backup database
- Monitor logs và metrics

### Docker (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "book_management_flask_v14.run"]
```

## Migration từ v13

Version 14 tương thích ngược với v13. Các thay đổi:

Thêm mới:
- Webhook notification system
- Webhook management API endpoints
- Demo webhook script

Không có breaking changes:
- Tất cả API v13 vẫn hoạt động
- Logging và monitoring không đổi

Để migrate:
1. Cập nhật code (đã có webhook)
2. Cấu hình webhook URLs (tùy chọn)
3. Deploy như bình thường

## Tài liệu tham khảo

### External Documentation

- Flask: https://flask.palletsprojects.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- Prometheus: https://prometheus.io/docs/
- Python Logging: https://docs.python.org/3/library/logging.html
- JWT: https://jwt.io/introduction
- OAuth2: https://oauth.net/2/
- OpenAPI: https://swagger.io/specification/

### Project Documentation

- openapi.yaml: OpenAPI specification
- requirements.txt: Python dependencies
- prometheus.yml: Prometheus configuration
- prometheus_alerts.yml: Alert rules

## Hỗ trợ

### Báo lỗi

- Kiểm tra logs: logs/book_management_error.log
- Xem metrics: http://localhost:5000/metrics
- Xem health: http://localhost:5000/health

### Development

```powershell
# Clone repo
git clone https://github.com/nmhung1294/INT3505E_02_demo.git

# Navigate to v14
cd INT3505E_02_demo/book_management_flask_v14

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run application
python -m book_management_flask_v14.run
```

## License

MIT License - See LICENSE file for details

## Version History

- v14 (Current): Webhook notifications
- v13: Logging & monitoring với Prometheus
- v12: API versioning và deprecation strategy
- v11: OpenAPI/Swagger integration
- v10: Authentication với JWT
- v9: OAuth2/OIDC integration
- Earlier: Basic CRUD operations

## Contributors

- nmhung1294 (Project Owner)

---

Cập nhật: 27/11/2025
Version: 14.0.0
