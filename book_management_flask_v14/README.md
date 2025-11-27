# Book Management System v13 - Logging & Monitoring

## What's New in v13

### Logging & Monitoring Implementation
Version 13 adds **production-grade logging and monitoring** with:

- **Structured Logging**: JSON format logs with Python's logging module
- **Prometheus Metrics**: HTTP, database, cache, and business metrics
- **Health Checks**: `/health` endpoint for service monitoring
- **Request Tracking**: Automatic tracking of all HTTP requests
- **Performance Monitoring**: Response time histograms and error tracking

See [LOGGING_MONITORING.md](./LOGGING_MONITORING.md) for complete documentation.

### Quick Start with Monitoring

```bash
# Install dependencies (includes prometheus-client)
pip install -r requirements.txt

# Run the application
python -m book_management_flask_v13.run

# View metrics
curl http://localhost:5000/metrics

# View health status
curl http://localhost:5000/health

# Check logs
cat logs/book_management.log
```

## API Versions

### Version 1 (Deprecated) ⚠️

```http
GET    /api/book_copies
POST   /api/book_copies
PUT    /api/book_copies/{id}
DELETE /api/book_copies/{id}
```

**Status**: Deprecated since November 13, 2025  
**Sunset**: June 1, 2026  
**Response headers include**:
```http
Deprecation: true
Sunset: 2026-06-01
Link: </api/v2/book-copies>; rel="successor-version"
Warning: 299 - "This API version is deprecated. Please migrate to v2"
```

### Version 2 (Current)
```http
GET    /api/v2/book-copies
GET    /api/v2/book-copies/{id}
POST   /api/v2/book-copies
PUT    /api/v2/book-copies/{id}
PATCH  /api/v2/book-copies/{id}
DELETE /api/v2/book-copies/{id}
```

**Enhancements**:
- 🚀 Embedded book title information (fewer API calls)
- 🔍 Advanced filtering: `?available=true&condition=Good&search=BC`
- 📊 Real-time borrowing status included
- 💬 Structured error responses with codes
- 📝 RESTful naming (kebab-case)
- ✨ PATCH support for partial updates
- 📍 Location headers in POST responses

## Quick Comparison

| Feature | v1 (Deprecated) | v2 (Current) |
|---------|----------------|--------------|
| Endpoint | `/api/book_copies` | `/api/v2/book-copies` |
| Naming | snake_case | camelCase |
| Response | `{items, page}` | `{data, pagination, meta}` |
| Embedded data | No |Yes (book titles) |
| Filtering | Limited |Advanced |
| Error format | Simple |Structured |
| GET single | No |Yes |
| PATCH method | No |Yes |
| Status info | No |Borrowing status |

## Example Responses

### v1 Response (Deprecated)
```json
{
  "items": [{
    "id": 1,
    "book_title_id": 5,
    "barcode": "BC001",
    "available": true,
    "condition": "Good"
  }],
  "page": {"page": 1, "size": 10}
}
```

### v2 Response (Current)
```json
{
  "data": [{
    "id": 1,
    "bookTitleId": 5,
    "barcode": "BC001",
    "available": true,
    "condition": "Good",
    "bookTitle": {
      "id": 5,
      "title": "Clean Code",
      "author": "Robert Martin"
    },
    "borrowingStatus": {
      "isBorrowed": false,
      "currentBorrowingId": null,
      "dueDate": null
    }
  }],
  "pagination": {"page": 1, "size": 10},
  "meta": {"version": "2.0"}
}
```

## Migration Guide

**📚 Complete documentation:**
- [API_VERSIONING.md](./API_VERSIONING.md) - Full migration guide
- [DEPRECATION_NOTICE.md](./DEPRECATION_NOTICE.md) - Important notices

**Quick migration steps:**

1. **Update URLs**: 
   ```javascript
   // Before
   fetch('/api/book_copies')
   
   // After
   fetch('/api/v2/book-copies')
   ```

2. **Update field names**:
   ```javascript
   // Before
   { book_title_id: 5 }
   
   // After
   { bookTitleId: 5 }
   ```

3. **Update response parsing**:
   ```javascript
   // Before
   data.items[0]
   
   // After
   data.data[0]
   ```

## Testing

### Run API Versioning Tests

```bash
# Make sure server is running on port 5000
python -m book_management_flask_v12.run

# In another terminal, run tests
python -m book_management_flask_v12.tests.test_api_versioning
```

This test suite demonstrates:
-v1 deprecation headers
-v2 enhanced features
-Response format differences
-API call efficiency comparison
-Error handling improvements

## Authentication & Authorization Flow

1. **Login/Register**:
   - User đăng nhập bằng email hoặc Google OAuth2
   - Server trả về JWT token
   - Token được lưu trong **HTTP-only cookie** với key `auth_token`
   - JavaScript **KHÔNG THỂ** truy cập token (bảo mật cao)

2. **Automatic Token Handling**:
   - Browser tự động gửi cookie với mọi request đến cùng domain
   - Không cần manually quản lý token trong JavaScript
   - Cookie được bảo vệ bởi `httponly`, `samesite` flags

3. **Token Validation**:
   - Backend kiểm tra cookie trong mỗi request
   - Frontend gọi `/auth/me` để verify authentication
   - Token có thời hạn 2 giờ

4. **Logout**:
   - Gọi API `/auth/logout` để xóa cookie
   - Server clear cookie bằng cách set `expires=0`
   - Redirect về trang login

## HTTP-only Cookie Security

**Bảo mật:**
- **XSS Protection**: JavaScript không thể đọc token
- **Automatic**: Browser tự động gửi cookie
- **Secure flags**: httponly, samesite, secure (HTTPS)
- **CSRF Protection**: SameSite=Lax ngăn CSRF attacks

**Trade-offs:**
- Không thể access token từ JavaScript
- Cần endpoint `/auth/me` để get user info
- Require same-origin hoặc proper CORS setup

## Cài đặt và Chạy

### Prerequisites
```bash
pip install flask flask-sqlalchemy pyjwt flasgger python-dotenv requests
```

### Chạy ứng dụng
Từ thư mục gốc của repository:
```bash
python -m book_management_flask_v10.run
```

Server sẽ chạy tại: **http://localhost:5000**


## So sánh các Version

| Feature | Version 8 | Version 9 | Version 10 |
|---------|-----------|-----------|------------|
| Token Storage | **localStorage** | **sessionStorage** | **HTTP-only Cookie** |
| UI | **Full Web UI** | **Full Web UI** | **Full Web UI** |
| Token Management | **Automatic** | **Automatic** | **Automatic** |
| Google OAuth | **Integrated UI** | **Integrated UI** | **Integrated UI** |
| Token Persistence | Persistent | Session Only | Session Only |
| Security Level | Medium | High | **Highest** |
| XSS Protection | No | No | **Yes** |
| JavaScript Access | Yes | Yes | **No** |
| CSRF Protection | Partial | Partial | **Yes (SameSite)** |

Version 10 minh họa:

1. **HTTP-only Cookies**: Server-side token management
2. **XSS Protection**: Token không thể bị steal qua JavaScript
3. **SameSite Cookie**: Protection against CSRF attacks
4. **Secure Cookie Flags**: Best practices for cookie security
5. **Backend Token Validation**: Token checked on server side
6. **Credential Management**: Proper use of `credentials: 'same-origin'`
7. **RESTful Auth Endpoint**: `/auth/me` for user verification
8. **Industry Standard**: Following OWASP recommendations

## Troubleshooting

**Cookie không được set?**
- Kiểm tra browser console (F12) → Application → Cookies
- Verify cookie path và domain
- Check SameSite compatibility (modern browsers)

**CORS issues?**
- Ensure `credentials: 'same-origin'` trong fetch calls
- Backend cần CORS headers nếu frontend khác domain
- Cookie requires same-origin by default

**Token không được gửi với request?**
- Verify `credentials: 'same-origin'` trong tất cả fetch calls
- Check cookie expiration time
- Ensure cookie path matches API path

**Làm sao debug cookie?**
- F12 → Application/Storage → Cookies
- Check cookie flags: HttpOnly, Secure, SameSite
- Network tab → Request Headers → Cookie

**Production deployment:**
- Set `secure=True` cho HTTPS
- Update `GOOGLE_OAUTH_REDIRECT_URI` 
- Consider `SameSite=Strict` for higher security

**Google OAuth không hoạt động?**
- Verify GOOGLE_CLIENT_ID và CLIENT_SECRET trong .env
- Check redirect URI match với Google Console
- Ensure popup không bị block

## Swagger UI

Swagger: http://localhost:5000/swagger
OpenAPI YAML (raw): http://127.0.0.1:5000/openapi.yaml