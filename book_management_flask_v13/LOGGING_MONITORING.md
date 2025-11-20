# Logging và Monitoring - Version 13

Version 13 đã được tích hợp logging và monitoring cơ bản sử dụng Python's logging module và Prometheus.

## Tính năng mới

### 1. Structured Logging

- **Module**: `logging_config.py`
- **Tính năng**:
  - JSON format logs cho machine parsing
  - Human-readable console output
  - Rotating file handlers (10MB max, 5 backups)
  - Separate error log files
  - Structured fields: timestamp, level, user_id, request_id, duration, endpoint, etc.

#### Log Levels
- `DEBUG`: Chi tiết operations (cache hits/misses, db queries)
- `INFO`: Normal operations (requests, authentications)
- `WARNING`: Potential issues (failed auth, unavailable books)
- `ERROR`: Operation failures
- `CRITICAL`: System failures

#### Log Files
Logs được lưu trong thư mục `logs/`:
- `book_management.log`: Tất cả logs (JSON format)
- `book_management_error.log`: Chỉ errors và above (JSON format)

### 2. Prometheus Metrics

- **Module**: `metrics.py`
- **Endpoint**: `GET /metrics`

#### HTTP Metrics
- `http_requests_total`: Tổng số HTTP requests (by method, endpoint, status)
- `http_request_duration_seconds`: Request duration histogram
- `http_errors_total`: Tổng số HTTP errors
- `http_requests_active`: Số requests đang xử lý

#### Database Metrics
- `db_operations_total`: Tổng số DB operations (by operation, table, status)
- `db_operation_duration_seconds`: DB operation duration histogram
- `db_errors_total`: Tổng số DB errors

#### Cache Metrics
- `cache_operations_total`: Tổng số cache operations
- `cache_hits_total`: Cache hits
- `cache_misses_total`: Cache misses
- `cache_size_bytes`: Cache size
- `cache_entries_total`: Số entries trong cache

#### Business Metrics
- `books_borrowed_total`: Tổng số sách được mượn
- `books_returned_total`: Tổng số sách được trả
- `active_borrowings_total`: Số borrowings đang active
- `user_registrations_total`: Tổng số đăng ký user
- `auth_attempts_total`: Tổng số authentication attempts (by status)

### 3. Health Check

- **Endpoint**: `GET /health`
- **Response**: `{"status": "healthy", "service": "book_management_api"}`

## Cài đặt

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure logging (optional)

Set environment variable `LOG_LEVEL`:

```bash
# In .env file
LOG_LEVEL=INFO
ENVIRONMENT=development
```

Các giá trị hợp lệ: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### 3. Run application

```bash
python -m book_management_flask_v13.run
```

## Sử dụng

### Xem Metrics

```bash
curl http://localhost:5000/metrics
```

Output (Prometheus format):
```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="api.get_book_titles",method="GET",status="200"} 15.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="api.get_book_titles",method="GET",status="200",le="0.005"} 10.0
...
```

### Health Check

```bash
curl http://localhost:5000/health
```

### Xem Logs

**Console Output** (human-readable):
```
2025-11-20 10:15:30 INFO     book_management: User logged in: user@example.com [user=1, endpoint=api.login]
2025-11-20 10:15:35 INFO     book_management: Book borrowed by user [user=1, borrowing=5, book_copy=3]
```

**Log Files** (JSON format):
```json
{
  "timestamp": "2025-11-20T10:15:30Z",
  "level": "INFO",
  "logger": "book_management",
  "message": "User logged in: user@example.com",
  "module": "api",
  "function": "login",
  "line": 235,
  "user_id": 1,
  "endpoint": "api.login"
}
```

## Tích hợp với Prometheus

### 1. Cài đặt Prometheus

Download từ: https://prometheus.io/download/

### 2. Configure Prometheus

Tạo file `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'book_management_api'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
```

### 3. Run Prometheus

```bash
./prometheus --config.file=prometheus.yml
```

Access Prometheus UI: http://localhost:9090

### 4. Example Queries

**Request rate**:
```promql
rate(http_requests_total[5m])
```

**Error rate**:
```promql
rate(http_errors_total[5m])
```

**Average request duration**:
```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

**Cache hit rate**:
```promql
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

**Active borrowings**:
```promql
active_borrowings_total
```

## Tích hợp với Grafana

### 1. Cài đặt Grafana

Download từ: https://grafana.com/grafana/download

### 2. Add Prometheus Data Source

- Vào Grafana UI (http://localhost:3000)
- Configuration → Data Sources → Add data source
- Chọn Prometheus
- URL: http://localhost:9090
- Save & Test

### 3. Import Dashboard

Tạo dashboard mới với các panels:

**HTTP Request Rate**:
- Query: `rate(http_requests_total[5m])`
- Visualization: Graph

**Error Rate**:
- Query: `rate(http_errors_total[5m])`
- Visualization: Graph

**Response Time (p95)**:
- Query: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- Visualization: Graph

**Cache Performance**:
- Query: `rate(cache_hits_total[5m])` và `rate(cache_misses_total[5m])`
- Visualization: Graph

**Active Borrowings**:
- Query: `active_borrowings_total`
- Visualization: Gauge

## Custom Logging

### Trong code của bạn

```python
from .logging_config import get_logger, log_request, log_db_operation

logger = get_logger()

# Log thông thường
logger.info("Something happened", extra={'user_id': user.id})

# Log request
log_request(logger, 'GET', '/api/books', 200, 45.2, user_id=1, ip_address='192.168.1.1')

# Log DB operation
log_db_operation(logger, 'CREATE', 'book', record_id=123, success=True)
```

### Custom Metrics

```python
from .metrics import (
    record_book_borrowed,
    record_book_returned,
    update_active_borrowings,
    record_cache_hit,
    record_cache_miss
)

# Record business events
record_book_borrowed()
record_book_returned()
update_active_borrowings(count)

# Record cache events
record_cache_hit()
record_cache_miss()
```

## Troubleshooting

### Logs không xuất hiện

- Kiểm tra `LOG_LEVEL` environment variable
- Kiểm tra quyền write vào thư mục `logs/`

### Metrics endpoint trả về empty

- Đảm bảo `prometheus-client` đã được install
- Kiểm tra console có báo lỗi import không

### Prometheus không scrape được metrics

- Kiểm tra API có đang chạy không
- Kiểm tra firewall có block port 5000 không
- Kiểm tra Prometheus config `prometheus.yml`

## Performance Impact

- **Logging**: Minimal overhead (~1-2ms per request)
- **Metrics**: Very low overhead (~0.5ms per request)
- **File I/O**: Asynchronous, không block requests

## Best Practices

1. **Log Level**: Sử dụng `INFO` cho production, `DEBUG` cho development
2. **Sensitive Data**: Không log passwords, tokens, credit cards
3. **Structured Fields**: Luôn thêm `user_id`, `request_id` vào logs
4. **Metrics**: Monitor error rates, response times, và business metrics
5. **Alerts**: Set up alerts cho error rate > 5%, response time > 1s

## Migration từ v12

Không có breaking changes. Chỉ cần:
1. Install dependencies mới: `pip install -r requirements.txt`
2. Application tự động enable logging và metrics

## Tài liệu tham khảo

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Grafana Documentation](https://grafana.com/docs/)
