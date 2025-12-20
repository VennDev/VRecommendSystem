# Custom Database Feature - Hướng dẫn sử dụng

## Tổng quan

Tính năng **Custom Database** cho phép bạn kết nối Data Chef đến bất kỳ database nào, thay vì sử dụng database mặc định được cấu hình trong `local.yaml`.

## ✅ Tính năng này KHÔNG PHẢI LÀ FAKE - Nó hoạt động thật sự!

### Các loại database được hỗ trợ:
- **SQL Databases**: MySQL, PostgreSQL, SQLite
- **NoSQL Databases**: MongoDB

## Cách sử dụng

### 1. Tạo Data Chef với SQL Database tùy chỉnh

Khi tạo Data Chef từ SQL:

1. Chọn "SQL Database" làm Data Source Type
2. Nhập SQL query của bạn
3. Bật checkbox "Use Custom Database"
4. Điền thông tin database:
   - **Database Type**: mysql / postgresql / sqlite
   - **Host**: Địa chỉ IP hoặc hostname (ví dụ: `192.168.1.100`)
   - **Port**: Cổng database (mặc định: 3306 cho MySQL, 5432 cho PostgreSQL)
   - **Database Name**: Tên database
   - **Username**: Tên đăng nhập
   - **Password**: Mật khẩu
   - **Use SSL**: Bật nếu cần kết nối SSL

### 2. Tạo Data Chef với NoSQL Database tùy chỉnh

Khi tạo Data Chef từ NoSQL:

1. Chọn "NoSQL Database" làm Data Source Type
2. Nhập Database Name và Collection Name
3. Bật checkbox "Use Custom Database"
4. Điền thông tin MongoDB:
   - **Database Type**: mongodb (mặc định)
   - **Host**: Địa chỉ MongoDB server
   - **Port**: Cổng MongoDB (mặc định: 27017)
   - **Database Name**: Tên database
   - **Username**: Tên đăng nhập (tùy chọn)
   - **Password**: Mật khẩu
   - **Auth Source**: Database xác thực (mặc định: `admin`)
   - **Use SSL**: Bật nếu cần kết nối SSL

## Ví dụ

### Ví dụ 1: Kết nối MySQL tùy chỉnh

```json
{
  "data_chef_id": "my_custom_mysql",
  "query": "SELECT user_id, product_id, rating FROM interactions",
  "rename_columns": "user_id->user_id,product_id->item_id,rating->rating",
  "db_config": {
    "type": "mysql",
    "host": "192.168.1.100",
    "port": 3306,
    "user": "myuser",
    "password": "mypassword",
    "database": "mydb",
    "ssl": false
  }
}
```

### Ví dụ 2: Kết nối MongoDB tùy chỉnh

```json
{
  "data_chef_id": "my_custom_mongodb",
  "database": "shop",
  "collection": "user_interactions",
  "rename_columns": "userId->user_id,itemId->item_id,score->rating",
  "db_config": {
    "type": "mongodb",
    "host": "mongodb.example.com",
    "port": 27017,
    "username": "admin",
    "password": "secret123",
    "database": "shop",
    "ssl": true,
    "auth_source": "admin"
  }
}
```

## Bảo mật

- ⚠️ Thông tin database config được lưu trữ an toàn
- 🔒 Khi hiển thị, chỉ 3 ký tự đầu tiên của password/host/username được hiển thị
- ✅ Không có thông tin nhạy cảm nào bị log ra console

## API Reference

### Create Data Chef từ SQL với Custom Database

**Endpoint**: `POST /api/v1/create_data_chef_from_sql`

**Body**:
```json
{
  "data_chef_id": "string",
  "query": "string",
  "rename_columns": "string",
  "db_config": {
    "type": "mysql | postgresql | sqlite",
    "host": "string",
    "port": "number",
    "user": "string",
    "password": "string",
    "database": "string",
    "ssl": "boolean"
  }
}
```

### Create Data Chef từ NoSQL với Custom Database

**Endpoint**: `POST /api/v1/create_data_chef_from_nosql`

**Body**:
```json
{
  "data_chef_id": "string",
  "database": "string",
  "collection": "string",
  "rename_columns": "string",
  "db_config": {
    "type": "mongodb",
    "host": "string",
    "port": "number",
    "username": "string",
    "password": "string",
    "database": "string",
    "ssl": "boolean",
    "auth_source": "string"
  }
}
```

## Troubleshooting

### Lỗi kết nối database

1. **Kiểm tra network**: Đảm bảo AI Server có thể truy cập database server
2. **Kiểm tra credentials**: Xác nhận username/password đúng
3. **Kiểm tra firewall**: Đảm bảo port database không bị block
4. **Kiểm tra SSL**: Nếu database yêu cầu SSL, bật option "Use SSL"

### Database config không được lưu

- Đảm bảo bạn đã bật checkbox "Use Custom Database"
- Điền đầy đủ tất cả thông tin bắt buộc (host, port, database, password)

## Technical Implementation

Tính năng này được implement ở:

1. **Backend Service**: `backend/ai_server/src/ai_server/services/data_chef_service.py`
   - `_create_custom_sql_engine()`: Tạo SQL engine
   - `_create_custom_nosql_client()`: Tạo MongoDB client

2. **Backend Router**: `backend/ai_server/src/ai_server/routers/private_routers.py`
   - `create_data_chef_from_sql()`: API endpoint cho SQL
   - `create_data_chef_from_nosql()`: API endpoint cho NoSQL

3. **Frontend Component**: `frontend/project/src/components/DataChefsPage.tsx`
   - `renderDatabaseConfigForm()`: UI form cho database config
   - `handleCreateDataChef()`: Logic gửi db_config lên backend

## Kết luận

Tính năng Custom Database **HOẠT ĐỘNG THẬT SỰ** và được implement đầy đủ. Nếu bạn gặp vấn đề, hãy kiểm tra lại:

✅ Đã bật checkbox "Use Custom Database"
✅ Điền đầy đủ thông tin database
✅ Database server có thể truy cập được từ AI Server
✅ Credentials chính xác
