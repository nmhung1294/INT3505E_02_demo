# Book Management System v8 - With LocalStorage Token Management-# Book Management Flask (v7) - Authentication & Authorization



1. **Login/Register**:

   - User đăng nhập bằng email hoặc Google OAuth2

   - Server trả về JWT token
   - Token được lưu trong `localStorage` với key `auth_token`

2. **Automatic Token Injection**:
   - Mọi API request tự động thêm header: `Authorization: Bearer <token>`
   - Không cần manually quản lý token cho mỗi request

3. **Token Validation**:
   - Frontend kiểm tra token expiration trước khi gửi request
   - Nếu token expired, tự động redirect về trang login
   - Token có thời hạn 2 giờ

4. **Logout**:
   - Xóa token khỏi localStorage
   - Redirect về trang login

## Cài đặt và Chạy

### Prerequisites
```bash
pip install flask flask-sqlalchemy pyjwt flasgger python-dotenv requests
```

### Chạy ứng dụng
Từ thư mục gốc của repository:
```bash
python -m book_management_flask_v8.run
```

Server sẽ chạy tại: **http://localhost:5000**


## So sánh với Version 7

| Feature | Version 7 | Version 8 |
|---------|-----------|-----------|
| Token Storage | Manual (client side) | **localStorage** |
| UI | Swagger only | **Full Web UI** |
| Token Management | Manual | **Automatic** |
| Google OAuth | API only | **Integrated UI** |

Version 8 minh họa:

1. **SPA Authentication**: Single Page Application với JWT
2. **LocalStorage API**: Browser storage cho client-side data
3. **Fetch API**: Modern way để gọi REST APIs
4. **Token Lifecycle**: Create → Store → Use → Validate → Expire
5. **OAuth2 Flow**: Integration với Google OAuth trong web app
6. **Frontend/Backend Separation**: Clean separation of concerns
7. **Error Handling**: Proper error handling và user feedback

## Troubleshooting

**Token không lưu?**
- Kiểm tra browser console (F12) xem có errors
- Verify localStorage không bị disabled
- Check same-origin policy

**Auto-redirect về login?**
- Token expired (after 2 hours)
- Token invalid hoặc bị xóa
- Check console logs

**Google OAuth không hoạt động?**
- Verify GOOGLE_CLIENT_ID và CLIENT_SECRET trong .env
- Check redirect URI match với Google Console
- Ensure popup không bị block

## Swagger UI

Swagger: http://localhost:5000/swagger
OpenAPI YAML (raw): http://127.0.0.1:5000/openapi.yaml