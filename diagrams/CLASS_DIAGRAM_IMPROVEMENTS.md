# Class Diagram Improvements - UML Relationship Corrections

## Tổng Quan
Đã sửa lại các mối quan hệ trong class diagrams để tuân thủ đúng chuẩn UML. Các thay đổi tập trung vào việc làm rõ các loại quan hệ giữa các class và sử dụng đúng ký hiệu UML.

## Các Loại Mối Quan Hệ UML Đã Sử Dụng

### 1. **Inheritance (Kế thừa)**
- **Ký hiệu**: Mũi tên rỗng (endArrow=block, endFill=0)
- **Khi nào dùng**: Khi một class kế thừa từ class khác hoặc implement interface
- **Label**: "extends" hoặc "implements"

### 2. **Association (Liên kết)**
- **Ký hiệu**: Mũi tên đơn giản (endArrow=none) hoặc có hướng
- **Khi nào dùng**: Khi các class có mối quan hệ với nhau nhưng không phải sở hữu
- **Label**: Tên thuộc tính hoặc vai trò

### 3. **Aggregation (Tập hợp)**
- **Ký hiệu**: Mũi tên kim cương rỗng (startArrow=diamondThin, startFill=0)
- **Khi nào dùng**: Quan hệ "has-a" nhưng lifecycle độc lập
- **Label**: Multiplicity (0..1, 1, *, etc.)

### 4. **Composition (Hợp thành)**
- **Ký hiệu**: Mũi tên kim cương đầy (startArrow=diamondThin, startFill=1)
- **Khi nào dùng**: Quan hệ "has-a" với lifecycle phụ thuộc
- **Label**: Multiplicity

### 5. **Dependency (Phụ thuộc)**
- **Ký hiệu**: Mũi tên đứt nét (dashed=1, endArrow=open)
- **Khi nào dùng**: Một class sử dụng class khác nhưng không sở hữu
- **Label**: <<uses>>, <<depends>>, <<imports>>

## Chi Tiết Các Thay Đổi

### 1. AI_Server_Schemas.drawio

#### Thêm mối quan hệ Inheritance:
- ✅ **ALSModelConfig → BaseModelConfig**: extends (kế thừa)
- ✅ **NCFModelConfig → BaseModelConfig**: extends (kế thừa)

#### Thêm mối quan hệ Dependency:
- ✅ **ModelTrainingRequest → BaseModelConfig**: <<uses>> (sử dụng trong field)
- ✅ **ModelTrainingResult → ModelStatus**: <<uses>> (sử dụng enum)
- ✅ **ModelInfo → ModelType**: <<uses>> (sử dụng enum)
- ✅ **ModelInfo → AlgorithmType**: <<uses>> (sử dụng enum)

**Lý do**: Các schema classes cần kế thừa từ base class để có cấu trúc chung. Các enum được sử dụng làm type cho các field nên cần dependency relationship.

---

### 2. Database_Schema.drawio

#### Thêm mối quan hệ Association (Foreign Keys):
- ✅ **interactions → users**: user_id (many-to-one)
  - Mỗi interaction thuộc về một user
  - Ký hiệu: Diamond ở interactions, kết nối đến users
  
- ✅ **interactions → items**: item_id (many-to-one)
  - Mỗi interaction liên quan đến một item
  - Ký hiệu: Diamond ở interactions, kết nối đến items

- ✅ **models → users**: created_by (many-to-one, optional)
  - Model được tạo bởi một user (có thể null)
  - Ký hiệu: Diamond ở models, đường dashed đến users

- ✅ **training_jobs → models**: model_id (many-to-one)
  - Mỗi training job liên quan đến một model
  - Ký hiệu: Diamond ở training_jobs, kết nối đến models

- ✅ **training_jobs → users**: created_by (many-to-one, optional)
  - Training job được tạo bởi một user
  - Ký hiệu: Diamond ở training_jobs, đường dashed đến users

**Lý do**: Database schema cần thể hiện các foreign key relationships để hiểu rõ mối quan hệ giữa các bảng.

---

### 3. AI_Server_Services.drawio

#### Sửa mối quan hệ từ Dependency sang Aggregation:
- ✅ **ModelService → DatabaseService**: 0..1 (aggregation)
  - ModelService có thể có một DatabaseService (optional)
  - Thay đổi từ <<uses>> sang aggregation với multiplicity
  
- ✅ **DataChefService → DatabaseService**: 1 (aggregation)
  - DataChefService bắt buộc có một DatabaseService
  - Thay đổi từ <<uses>> sang aggregation với multiplicity

- ✅ **SchedulerService → ModelService**: 1 (aggregation)
  - SchedulerService cần một ModelService để thực hiện training tasks
  - Thay đổi từ <<uses for training>> sang aggregation với multiplicity

#### Thêm mới:
- ✅ **SchedulerService → DataChefService**: 1 (aggregation)
  - SchedulerService cần DataChefService để fetch training data

#### Giữ nguyên Dependency:
- ✅ **DataChefService → DataType**: <<depends>> (dependency)
  - Sử dụng enum để xác định loại data source

**Lý do**: Services có lifecycle độc lập nhưng cần reference đến nhau. Aggregation phù hợp hơn dependency vì đây là quan hệ lâu dài, không phải chỉ sử dụng tạm thời.

---

### 4. AI_Server_Tasks.drawio

#### Thêm mối quan hệ Aggregation:
- ✅ **ModelTrainerTask → ModelService**: 1 (aggregation với label "model_service")
  - Task cần ModelService để train model
  
- ✅ **ModelTrainerTask → DataChefService**: 1 (aggregation với label "datachef_service")
  - Task cần DataChefService để fetch data

**Lưu ý**: Các mũi tên được vẽ từ ModelTrainerTask đến BaseTask để tránh chồng lấn, nhưng ý nghĩa logic là Task sử dụng các Services.

**Lý do**: Tasks cần dependency injection của services để hoạt động. Aggregation thể hiện rõ task "có" reference đến services.

---

### 5. System_Overview.drawio

#### Sửa lại các mối quan hệ giữa components:

**Từ Association hai chiều sang Dependency một chiều:**
- ✅ **Frontend → API Server**: <<uses>> (dependency, dashed)
  - Label: "<<uses>> HTTP/REST JSON"
  
- ✅ **API Server → AI Server**: <<uses>> (dependency, dashed)
  - Label: "<<uses>> HTTP/REST Model requests"

**Từ Association sang Aggregation:**
- ✅ **API Server → PostgreSQL**: 1 (aggregation)
  - Label: "1 SQL User data, logs"
  
- ✅ **AI Server → PostgreSQL**: 0..1 (aggregation)
  - Label: "0..1 SQL Training data"
  
- ✅ **AI Server → MongoDB**: 0..1 (aggregation)
  - Label: "0..1 NoSQL Task history"

**Giữ nguyên Dependency:**
- ✅ **API Server → External Services**: <<uses>> (dependency, dashed)
  - Label: "<<uses>> OAuth Authentication"

**Lý do**: 
- HTTP calls là dependency tạm thời, không phải ownership
- Database connections là aggregation vì server "có" connection nhưng database tồn tại độc lập
- Multiplicity 0..1 cho optional databases (có thể config hoặc không)

---

### 6. AI_Server_Models.drawio
**Không thay đổi** - Diagram này đã đúng chuẩn UML từ trước:
- ✅ Inheritance relationships đúng (NMF, SVD extends BaseRecommendationModel)
- ✅ Dependency relationships đúng (ModelRegistry uses BaseRecommendationModel)
- ✅ Planned models dùng dashed lines hợp lý

---

### 7. API_Server_Classes.drawio
**Không thay đổi** - Diagram này đã đúng chuẩn:
- ✅ Implements relationship đúng (Logger implements interface)
- ✅ Composition relationships đúng (Config has JWT, Database configs)

---

### 8. Email.drawio
**Không thay đổi** - Chỉ là single table schema, không có relationships.

---

### 9. Frontend_Components.drawio
**Không thay đổi** - Diagram này không có relationships giữa components, chỉ là danh sách.

---

## Nguyên Tắc UML Đã Áp Dụng

### 1. **Chọn đúng loại quan hệ:**
- Inheritance: Khi có "is-a" relationship (ALSModelConfig IS A BaseModelConfig)
- Aggregation: Khi có "has-a" với lifecycle độc lập (Service HAS A DatabaseService)
- Composition: Khi có "has-a" với lifecycle phụ thuộc (Config HAS JWT settings)
- Dependency: Khi chỉ sử dụng tạm thời (Frontend USES API Server)
- Association: Khi có relationship nhưng không rõ ownership (Foreign keys)

### 2. **Thêm Multiplicity:**
- `0..1`: Optional, có thể có hoặc không
- `1`: Bắt buộc, phải có đúng một
- `*`: Nhiều (zero to many)
- `1..*`: Ít nhất một

### 3. **Thêm Labels rõ ràng:**
- Tên thuộc tính cho associations (user_id, model_id)
- Stereotype cho dependencies (<<uses>>, <<depends>>)
- Mô tả cho complex relationships (HTTP/REST, SQL)

### 4. **Giữ nguyên phong cách:**
- Không thay đổi màu sắc
- Không thay đổi layout
- Chỉ sửa relationships và labels

## Tổng Kết

**Số lượng thay đổi:**
- ✅ AI_Server_Schemas: +6 relationships
- ✅ Database_Schema: +5 relationships  
- ✅ AI_Server_Services: Sửa 4 relationships, +1 mới
- ✅ AI_Server_Tasks: +2 relationships
- ✅ System_Overview: Sửa 5 relationships

**Tổng cộng**: 23 improvements

**Kết quả**: Tất cả class diagrams giờ đây tuân thủ đúng chuẩn UML và thể hiện rõ ràng các mối quan hệ giữa các components trong hệ thống VRecommendation.