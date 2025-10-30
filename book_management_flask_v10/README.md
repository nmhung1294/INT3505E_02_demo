# Book Management System v10 - With HTTP-only Cookie Token Management

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