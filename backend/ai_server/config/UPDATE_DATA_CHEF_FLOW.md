# Data Chef Update Flow - Database Config

## 🔄 Flow cập nhật Data Chef

### 1. Khi user mở Edit Modal

**Frontend** (`DataChefsPage.tsx` - dòng 124-167):

```typescript
const handleEditDataChef = async (dataChef: DataChef) => {
  // 1. Load basic info
  setSelectedDataChef(dataChef);
  setSelectedType(dataChef.type);
  setFormData({ ... });

  // 2. Load db_config nếu có
  if (dataChef.db_config) {
    setUseCustomDb(true);  // ← Bật custom DB flag
    setDbConfig({
      type: dataChef.db_config.type,
      host: dataChef.db_config.host,
      port: dataChef.db_config.port,
      user: dataChef.db_config.user || dataChef.db_config.username,
      password: dataChef.db_config.password,
      database: dataChef.db_config.database,
      ssl: dataChef.db_config.ssl,
      auth_source: dataChef.db_config.auth_source,
    });
  } else {
    setUseCustomDb(false);  // ← Tắt custom DB flag
    setDbConfig({ ... });   // ← Reset to default
  }

  setShowEditModal(true);
};
```

### 2. User chỉnh sửa thông tin

User có thể:
- ✏️ Thay đổi query/path/collection
- ✏️ Thay đổi database config (host, port, user, password, etc.)
- 🔄 Bật/tắt "Use Custom Database" checkbox
- ✏️ Thay đổi database type (MySQL → PostgreSQL → MongoDB)

### 3. Khi user nhấn "Update Data Chef"

**Frontend** (`DataChefsPage.tsx` - dòng 169-250):

```typescript
const handleUpdateDataChef = async (e: React.FormEvent) => {
  const updateData: Partial<DataChef> = {
    type: selectedType,
    rename_columns: formData.renameColumns,
  };

  switch (selectedType) {
    case "sql":
      updateData.query = formData.query;

      if (useCustomDb) {
        // ← Gửi db_config nếu custom DB được bật
        updateData.db_config = {
          type: dbConfig.type,
          host: dbConfig.host,
          port: dbConfig.port,
          password: dbConfig.password,
          database: dbConfig.database,
          ssl: dbConfig.ssl,
          user: dbConfig.user,  // hoặc username cho MongoDB
        };
      } else {
        // ← Xóa db_config nếu custom DB bị tắt
        updateData.db_config = null;
      }
      break;
  }

  // Gửi request lên backend
  await apiService.editDataChef(selectedDataChef.id, updateData);
};
```

### 4. Backend nhận request

**Backend Router** (`private_routers.py` - dòng 682-696):

```python
@router.put("/edit_data_chef/{data_chef_id}")
def edit_data_chef(data_chef_id: str, request: DataChefEditRequest):
    data_chef = data_chef_service.DataChefService()
    data_chef.edit_data_chef(data_chef_id, request.values)
    return {"message": f"Data chef {data_chef_id} edited successfully."}
```

**Backend Service** (`data_chef_service.py` - dòng 793-822):

```python
def edit_data_chef(self, name: str, config_dict: dict) -> None:
    # 1. Load existing config
    existing_cfg = Config().get_config_safe("restaurant_data")
    existing_dict = OmegaConf.to_object(existing_cfg)

    # 2. Update config
    for key, value in config_dict.items():
        if value is None:
            # Xóa key nếu value = None
            existing_dict[name].pop(key, None)
        else:
            # Cập nhật key với value mới
            existing_dict[name][key] = value

    # 3. Lưu vào file restaurant_data.yaml
    Config().set_config_with_dict("restaurant_data", existing_dict)
```

### 5. File YAML được cập nhật

**File**: `backend/ai_server/config/restaurant_data.yaml`

## 📊 Ví dụ Update Scenarios

### Scenario 1: Thêm Custom Database vào Data Chef đã có

**Trước khi update** (`restaurant_data.yaml`):
```yaml
data_a:
  type: sql
  query: SELECT * FROM interactions
  rename_columns: userId->user_id,productId->item_id
```

**User actions**:
1. Click Edit button on `data_a`
2. Bật "Use Custom Database" checkbox
3. Nhập database config:
   - Type: MySQL
   - Host: 192.168.2.12
   - Port: 3306
   - User: admin
   - Password: secret123
   - Database: shop
   - SSL: false
4. Click "Update Data Chef"

**Sau khi update** (`restaurant_data.yaml`):
```yaml
data_a:
  type: sql
  query: SELECT * FROM interactions
  rename_columns: userId->user_id,productId->item_id
  db_config:                    # ← Được thêm vào!
    type: mysql
    host: 192.168.2.12
    port: 3306
    user: admin
    password: secret123
    database: shop
    ssl: false
```

### Scenario 2: Sửa Custom Database hiện có

**Trước khi update**:
```yaml
data_a:
  type: sql
  query: SELECT * FROM interactions
  rename_columns: userId->user_id,productId->item_id
  db_config:
    type: mysql
    host: 192.168.2.12
    port: 3306
    user: admin
    password: secret123
    database: shop
    ssl: false
```

**User actions**:
1. Click Edit button
2. "Use Custom Database" checkbox đã được tự động check (vì có db_config)
3. Thay đổi:
   - Host: 192.168.2.12 → **10.0.0.50**
   - Password: secret123 → **newpassword456**
4. Click "Update Data Chef"

**Sau khi update**:
```yaml
data_a:
  type: sql
  query: SELECT * FROM interactions
  rename_columns: userId->user_id,productId->item_id
  db_config:
    type: mysql
    host: 10.0.0.50          # ← Đã thay đổi!
    port: 3306
    user: admin
    password: newpassword456  # ← Đã thay đổi!
    database: shop
    ssl: false
```

### Scenario 3: Xóa Custom Database (quay về default)

**Trước khi update**:
```yaml
data_a:
  type: sql
  query: SELECT * FROM interactions
  rename_columns: userId->user_id,productId->item_id
  db_config:
    type: mysql
    host: 192.168.2.12
    port: 3306
    user: admin
    password: secret123
    database: shop
    ssl: false
```

**User actions**:
1. Click Edit button
2. **Tắt** "Use Custom Database" checkbox
3. Click "Update Data Chef"

**Sau khi update**:
```yaml
data_a:
  type: sql
  query: SELECT * FROM interactions
  rename_columns: userId->user_id,productId->item_id
  # ← db_config đã bị xóa hoàn toàn!
```

### Scenario 4: Đổi Database Type (MySQL → PostgreSQL)

**Trước khi update**:
```yaml
data_a:
  type: sql
  query: SELECT * FROM interactions
  db_config:
    type: mysql
    host: 192.168.2.12
    port: 3306
    user: admin
    password: secret123
    database: shop
    ssl: false
```

**User actions**:
1. Click Edit button
2. Trong Database Config, đổi Type: MySQL → **PostgreSQL**
3. Port tự động đổi: 3306 → **5432**
4. Click "Update Data Chef"

**Sau khi update**:
```yaml
data_a:
  type: sql
  query: SELECT * FROM interactions
  db_config:
    type: postgresql         # ← Đã đổi!
    host: 192.168.2.12
    port: 5432              # ← Đã đổi!
    user: admin
    password: secret123
    database: shop
    ssl: false
```

## 🔐 Security Notes

### Password Masking

Khi hiển thị Data Chef info (View Details), password được mask:

```typescript
// Frontend hiển thị
Password: sec********  // ← Chỉ hiển thị 3 ký tự đầu

// Backend trả về (API response)
{
  "password": "sec********"  // ← Đã được mask
}

// Lưu trong file YAML (backend internal)
password: secret123  // ← Plain text
```

### Password Update Logic

**⚠️ Lưu ý quan trọng**: Hiện tại password được update theo logic:

1. User nhập password mới → Password được cập nhật
2. User để trống password → Password cũ được giữ nguyên (❌ CHƯA implement!)

**TODO**: Cần implement logic để giữ password cũ nếu user không nhập password mới.

## ✅ Testing Checklist

- [ ] Update query của SQL Data Chef
- [ ] Thêm custom database vào Data Chef không có custom DB
- [ ] Sửa custom database hiện có
- [ ] Xóa custom database (quay về default)
- [ ] Đổi database type (MySQL → PostgreSQL → MongoDB)
- [ ] Update NoSQL Data Chef với custom database
- [ ] Tắt Custom Database và kiểm tra db_config đã bị xóa
- [ ] Kiểm tra file `restaurant_data.yaml` sau mỗi lần update
- [ ] Verify model training vẫn hoạt động sau khi update
- [ ] Test với masked password từ API response

## 🐛 Known Issues

### Issue 1: Password bị ghi đè khi không nhập mới

**Problem**: Nếu user không nhập password mới khi edit, password cũ bị mất.

**Solution**: Cần implement logic:
```typescript
if (dbConfig.password === "" || dbConfig.password === "***") {
  // Không gửi password field → backend giữ nguyên password cũ
  delete updateData.db_config.password;
}
```

### Issue 2: Masked password không thể edit

**Problem**: Khi load từ API, password đã bị mask (e.g., "sec********"), user không thể edit được.

**Solution**:
1. Backend trả về flag `password_is_masked: true`
2. Frontend hiển thị placeholder "Enter new password (leave blank to keep current)"
3. Chỉ gửi password lên backend nếu user nhập mới

## 📝 Summary

✅ **Đã fix**:
- Frontend load db_config vào state khi mở edit modal
- Frontend gửi db_config khi update (nếu useCustomDb = true)
- Frontend gửi db_config = null khi tắt custom DB
- Backend xóa hoàn toàn db_config key khi nhận value = null
- Database config được lưu vào `restaurant_data.yaml`

⚠️ **Cần fix thêm**:
- Password update logic (giữ password cũ nếu không nhập mới)
- Masked password handling
