# Hướng Dẫn Deploy Lên Railway (Tiếng Việt)

## Vấn Đề Đã Khắc Phục

Lỗi deployment ban đầu trên Railway:
```
Healthcheck failed!
1/1 replicas never became healthy!
```

### Nguyên Nhân

1. **SECRET_KEY bắt buộc**: Ứng dụng yêu cầu SECRET_KEY nhưng không có giá trị mặc định
2. **Database connection lỗi**: App crash khi không kết nối được database lúc khởi động
3. **PORT không đúng**: App không đọc PORT từ Railway environment
4. **reload=True**: Không phù hợp cho production

### Giải Pháp Đã Áp Dụng

✅ **Thêm giá trị mặc định cho SECRET_KEY** (`app/config.py`)
- Giá trị mặc định: `dev-secret-key-change-in-production`
- Ứng dụng có thể khởi động ngay cả khi không set SECRET_KEY
- ⚠️ **CHÚ Ý**: Phải đổi SECRET_KEY trong production!

✅ **Hỗ trợ PORT từ Railway** (`run.py`)
- Đọc PORT từ environment variable
- Tắt `reload=True` cho production
- Ứng dụng tự động bind vào port Railway chỉ định

✅ **Database lazy loading** (`app/database.py`)
- Database engine chỉ tạo khi cần thiết
- Không crash nếu DATABASE_URL chưa có
- Ứng dụng vẫn khởi động được

✅ **Error handling cải thiện** (`app/main.py`)
- Database lỗi chỉ log warning, không crash app
- Health check endpoint `/` hoạt động độc lập
- Ứng dụng start trước, database init sau

## Cách Deploy Lên Railway

### Bước 1: Tạo Project Railway

1. Truy cập https://railway.app
2. Đăng nhập và tạo project mới
3. Chọn "Deploy from GitHub repo"
4. Chọn repository của bạn

### Bước 2: Thêm PostgreSQL Database

1. Trong Railway project, click **New** → **Database** → **Add PostgreSQL**
2. Railway tự động tạo biến `DATABASE_URL`

### Bước 3: Cấu Hình Environment Variables

Vào **Settings** → **Variables** và thêm:

#### Bắt Buộc:

```env
SECRET_KEY=<chuỗi-ngẫu-nhiên-bảo-mật>
```

Tạo SECRET_KEY an toàn:
```bash
# Cách 1: OpenSSL
openssl rand -hex 32

# Cách 2: Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### Tùy Chọn:

```env
CORS_ORIGINS=https://your-frontend-domain.com
ENVIRONMENT=production
DEBUG=false
```

### Bước 4: Deploy

Railway sẽ tự động:
1. ✅ Detect `Dockerfile.railway`
2. ✅ Build Docker image
3. ✅ Deploy ứng dụng
4. ✅ Chạy health check tại endpoint `/`
5. ✅ Nếu health check pass → Deployment thành công! 🎉

### Bước 5: Kiểm Tra Deployment

Xem logs trong Railway dashboard để đảm bảo:
- ✅ Build thành công
- ✅ Ứng dụng start không lỗi
- ✅ Health check pass
- ✅ Database kết nối thành công

## API Endpoints

Sau khi deploy thành công, bạn có thể truy cập:

- **Root (Health Check)**: `https://your-app.railway.app/`
- **Health**: `https://your-app.railway.app/health`
- **API Documentation**: `https://your-app.railway.app/docs`
- **ReDoc**: `https://your-app.railway.app/redoc`

## Troubleshooting

### Health Check Vẫn Fail

**Kiểm tra logs để tìm lỗi cụ thể:**

1. Vào Railway Dashboard → Project → Logs
2. Xem phần startup logs

**Các lỗi phổ biến:**

#### 1. Secret Key Error
```
ValidationError: SECRET_KEY required
```
**Giải pháp**: Đã fix! Giờ có giá trị mặc định.

#### 2. Database Connection Error
```
⚠️  Database initialization failed
```
**Giải pháp**: Đã fix! App vẫn start được, database lỗi chỉ log warning.

#### 3. Port Binding Error
```
Address already in use
```
**Giải pháp**: Đã fix! App tự động đọc PORT từ Railway.

### Kiểm Tra Health Check Thủ Công

```bash
# Thay your-app bằng tên app Railway của bạn
curl https://your-app.railway.app/

# Response mong đợi:
{
  "status": "ok",
  "service": "FocusFlow API",
  "version": "1.0.0"
}
```

### Database Không Kết Nối

**Triệu chứng**: Endpoints auth, focus, recordings trả về lỗi 500

**Giải pháp**:
1. Kiểm tra PostgreSQL đã được add chưa
2. Verify `DATABASE_URL` trong Environment Variables
3. Đảm bảo database và app cùng region

## Lưu Ý Bảo Mật

⚠️ **QUAN TRỌNG**: Đổi SECRET_KEY trong production!

SECRET_KEY mặc định (`dev-secret-key-change-in-production`) chỉ dùng cho development.

**Tạo SECRET_KEY an toàn:**

```bash
# Linux/Mac
openssl rand -hex 32

# Python (works everywhere)
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Sau đó set trong Railway:
1. Railway Dashboard → Project → Variables
2. Thêm `SECRET_KEY=<chuỗi-vừa-tạo>`
3. Railway sẽ tự động redeploy

## Cập Nhật Code

Khi bạn push code mới lên GitHub, Railway tự động:
1. Detect thay đổi
2. Rebuild Docker image
3. Deploy version mới
4. Chạy health check
5. Nếu OK → Chuyển traffic sang version mới

```bash
git add .
git commit -m "Your changes"
git push origin main
```

## Kết Luận

Các thay đổi đã được thực hiện để đảm bảo:
- ✅ Ứng dụng start được ngay cả không có database
- ✅ Health check hoạt động độc lập
- ✅ Hỗ trợ Railway PORT environment variable
- ✅ Error handling tốt hơn với logging rõ ràng
- ✅ Production-ready configuration

Deployment của bạn giờ sẽ thành công! 🚀

## Liên Hệ Hỗ Trợ

Nếu vẫn gặp vấn đề:
1. Kiểm tra Railway deployment logs
2. Verify tất cả environment variables đã set đúng
3. Test database connectivity
4. Review application startup logs
