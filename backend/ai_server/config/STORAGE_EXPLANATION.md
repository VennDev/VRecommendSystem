# Database Configuration Storage - Chi tiết lưu trữ

## 📂 Nơi lưu trữ

Database config của Data Chef được lưu vào file:

```
backend/ai_server/config/restaurant_data.yaml
```

## 📝 Cấu trúc lưu trữ

### Khi KHÔNG sử dụng Custom Database

File `restaurant_data.yaml`:

```yaml
my_data_chef:
  type: sql
  query: SELECT * FROM interactions
  rename_columns: userId->user_id,productId->item_id,rating->rating
```

### Khi SỬ DỤNG Custom Database

File `restaurant_data.yaml`:

```yaml
my_custom_data_chef:
  type: sql
  query: SELECT * FROM interactions
  rename_columns: userId->user_id,productId->item_id,rating->rating
  db_config:                          # ← Database config được lưu ở đây!
    type: mysql
    host: 192.168.1.100
    port: 3306
    user: myuser
    password: mypassword              # ← Password được lưu PLAIN TEXT
    database: mydb
    ssl: false
```

## 🔄 Flow lưu trữ

```
1. User nhập database config trên Frontend
   ↓
2. Frontend gửi db_config lên Backend API
   ↓
3. Backend Router nhận request.db_config
   ↓
4. DataChefService.create_data_chef_sql()
   ↓
5. _merge_config() được gọi
   ↓
6. Config().set_config_with_dict("restaurant_data", data)
   ↓
7. File được lưu vào: backend/ai_server/config/restaurant_data.yaml
```

## 💾 Code lưu trữ

**File**: `backend/ai_server/src/ai_server/services/data_chef_service.py`

```python
def create_data_chef_sql(self, name: str, query: str, rename_columns: str,
                         db_config: Optional[Dict[str, Any]] = None) -> None:
    new_data = {
        "type": DataType.SQL.value,
        "query": query,
        "rename_columns": rename_columns,
    }

    if db_config:
        new_data["db_config"] = db_config  # ← Lưu db_config vào data

    self._merge_config(name, new_data)  # ← Lưu vào file YAML
```

**File**: `backend/ai_server/src/ai_server/config/config.py`

```python
def set_config_with_dict(self, name: str, config_dict: Dict[str, Any]) -> None:
    # Path: backend/ai_server/config/{name}.yaml
    config_file_path = self.config_path / f"{name}.yaml"

    # Lưu vào file YAML
    with open(config_file_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
```

## 📊 Ví dụ thực tế

### Ví dụ 1: MySQL Custom Database

**Input (từ Frontend):**
```json
{
  "data_chef_id": "my_mysql",
  "query": "SELECT user_id, item_id, rating FROM interactions",
  "rename_columns": "user_id->user_id,item_id->item_id,rating->rating",
  "db_config": {
    "type": "mysql",
    "host": "192.168.2.12",
    "port": 3306,
    "user": "admin",
    "password": "pokiwar0981",
    "database": "shop",
    "ssl": false
  }
}
```

**Output (trong `restaurant_data.yaml`):**
```yaml
my_mysql:
  type: sql
  query: SELECT user_id, item_id, rating FROM interactions
  rename_columns: user_id->user_id,item_id->item_id,rating->rating
  db_config:
    type: mysql
    host: 192.168.2.12
    port: 3306
    user: admin
    password: pokiwar0981
    database: shop
    ssl: false
```

### Ví dụ 2: MongoDB Custom Database

**Input:**
```json
{
  "data_chef_id": "my_mongodb",
  "database": "shop",
  "collection": "orders",
  "rename_columns": "userId->user_id,itemId->item_id",
  "db_config": {
    "type": "mongodb",
    "host": "localhost",
    "port": 27017,
    "username": "admin",
    "password": "admin123",
    "database": "shop",
    "ssl": false,
    "auth_source": "admin"
  }
}
```

**Output (trong `restaurant_data.yaml`):**
```yaml
my_mongodb:
  type: nosql
  database: shop
  collection: orders
  rename_columns: userId->user_id,itemId->item_id
  db_config:
    type: mongodb
    host: localhost
    port: 27017
    username: admin
    password: admin123
    database: shop
    ssl: false
    auth_source: admin
```

## 🔐 Bảo mật

### ⚠️ Lưu ý quan trọng:

1. **Password được lưu PLAIN TEXT** trong `restaurant_data.yaml`
2. File này **KHÔNG nên** commit vào Git
3. Chỉ **AI Server** có quyền đọc file này
4. Khi hiển thị qua API, password sẽ được **mask** (chỉ hiện 3 ký tự đầu)

### Masking khi hiển thị

**File**: `data_chef_service.py`

```python
def _mask_db_config(db_config: Dict[str, Any]) -> Dict[str, Any]:
    masked_config = db_config.copy()

    # Mask password: "mypassword" -> "myp*******"
    if "password" in masked_config:
        masked_config["password"] = _mask_sensitive_value(masked_config["password"], 3)

    # Mask host: "192.168.1.100" -> "192**********"
    if "host" in masked_config:
        masked_config["host"] = _mask_sensitive_value(masked_config["host"], 3)

    return masked_config
```

## 🔍 Kiểm tra file

Để xem database config đã được lưu:

```bash
cat backend/ai_server/config/restaurant_data.yaml
```

Hoặc:

```bash
# Xem toàn bộ data chefs
grep -A 10 "db_config:" backend/ai_server/config/restaurant_data.yaml
```

## 📋 Tổng kết

| Thông tin | Chi tiết |
|-----------|----------|
| **File lưu trữ** | `backend/ai_server/config/restaurant_data.yaml` |
| **Format** | YAML |
| **Encoding** | UTF-8 |
| **Quyền truy cập** | Chỉ AI Server |
| **Bảo mật** | Plain text trong file, masked khi hiển thị API |
| **Git** | Không nên commit (thêm vào .gitignore) |

✅ Database config được lưu **ĐẦY ĐỦ** và **THẬT SỰ** vào file `restaurant_data.yaml`!
