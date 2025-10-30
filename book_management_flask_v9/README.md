# Book Management System v9 - With SessionStorage Token Management

## Authentication & Authorization Flow

1. **Login/Register**:

   - User đăng nhập bằng email hoặc Google OAuth2

   - Server trả về JWT token
   - Token được lưu trong `sessionStorage` với key `auth_token`

2. **Automatic Token Injection**:
   - Mọi API request tự động thêm header: `Authorization: Bearer <token>`
   - Không cần manually quản lý token cho mỗi request

3. **Token Validation**:
   - Frontend kiểm tra token expiration trước khi gửi request
   - Nếu token expired, tự động redirect về trang login
   - Token có thời hạn 2 giờ

4. **Logout**:
   - Xóa token khỏi sessionStorage
   - Redirect về trang login

## SessionStorage vs LocalStorage

**SessionStorage** (v9):
- Token chỉ tồn tại trong phiên làm việc hiện tại
- Token tự động bị xóa khi đóng tab/browser
- Bảo mật hơn - token không tồn tại lâu dài trên máy client
- Mỗi tab có sessionStorage riêng

**LocalStorage** (v8):
- Token tồn tại vĩnh viễn cho đến khi bị xóa
- Token vẫn còn sau khi đóng browser
- Tiện lợi hơn - không cần login lại
- Chia sẻ giữa các tab

## Cài đặt và Chạy

### Prerequisites
```bash
pip install flask flask-sqlalchemy pyjwt flasgger python-dotenv requests
```

### Chạy ứng dụng
Từ thư mục gốc của repository:
```bash
python -m book_management_flask_v9.run
```

Server sẽ chạy tại: **http://localhost:5000**


## So sánh với Version 7 & 8

| Feature | Version 7 | Version 8 | Version 9 |
|---------|-----------|-----------|-----------|
| Token Storage | Manual (client side) | **localStorage** | **sessionStorage** |
| UI | Swagger only | **Full Web UI** | **Full Web UI** |
| Token Management | Manual | **Automatic** | **Automatic** |
| Google OAuth | API only | **Integrated UI** | **Integrated UI** |
| Token Persistence | N/A | Persistent | **Session Only** |

Version 9 minh họa:

1. **SPA Authentication**: Single Page Application với JWT
2. **SessionStorage API**: Browser session storage cho client-side data
3. **Fetch API**: Modern way để gọi REST APIs
4. **Token Lifecycle**: Create → Store → Use → Validate → Expire
5. **OAuth2 Flow**: Integration với Google OAuth trong web app
6. **Frontend/Backend Separation**: Clean separation of concerns
7. **Error Handling**: Proper error handling và user feedback
8. **Session-based Security**: Token chỉ tồn tại trong phiên làm việc

## Troubleshooting

**Token không lưu?**
- Kiểm tra browser console (F12) xem có errors
- Verify sessionStorage không bị disabled
- Check same-origin policy

**Auto-redirect về login khi mở tab mới?**
- Đây là behavior bình thường của sessionStorage
- Mỗi tab có sessionStorage riêng
- Cần login lại cho mỗi tab mới

**Auto-redirect về login sau khi đóng/mở browser?**
- Token expired (after 2 hours) hoặc
- Browser bị đóng (sessionStorage bị xóa)
- Check console logs

**Google OAuth không hoạt động?**
- Verify GOOGLE_CLIENT_ID và CLIENT_SECRET trong .env
- Check redirect URI match với Google Console
- Ensure popup không bị block

## Swagger UI

Swagger: http://localhost:5000/swagger
OpenAPI YAML (raw): http://127.0.0.1:5000/openapi.yaml