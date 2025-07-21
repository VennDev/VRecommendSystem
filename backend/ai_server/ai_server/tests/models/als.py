# Cài đặt thư viện Microsoft Recommenders
# pip install recommenders

import pandas as pd
import numpy as np
from recommenders.datasets import movielens
from recommenders.models.sar import SAR
from recommenders.evaluation.python_evaluation import map_at_k, ndcg_at_k, precision_at_k, recall_at_k
from recommenders.utils.timer import Timer
from recommenders.utils.constants import SEED

# 1. VÍ DỤ CƠ BẢN VỚI SAR (Smart Adaptive Recommendations)
print("=== Ví dụ 1: Sử dụng thuật toán SAR ===")

# Tải dữ liệu MovieLens 100K
data = movielens.load_pandas_df(
    size='100k',
    header=['UserID', 'ItemID', 'Rating', 'Timestamp']
)

print(f"Dữ liệu có {data.shape[0]} dòng và {data.shape[1]} cột")
print(data.head())

# Chia dữ liệu thành train/test (80/20)
from recommenders.datasets.python_splitters import python_random_split

train, test = python_random_split(data, ratio=0.8, seed=SEED)
print(f"Train: {train.shape[0]} dòng, Test: {test.shape[0]} dòng")

# Khởi tạo và huấn luyện mô hình SAR
model = SAR(
    similarity_type="jaccard",
    time_decay_coefficient=30,
    time_now=None,
    timedecay_formula=True
)

with Timer() as t:
    model.fit(train)
print(f"Thời gian huấn luyện: {t.interval:.2f} giây")

# Tạo dự đoán top-k recommendations
top_k = model.recommend_k_items(test, top_k=10, remove_seen=True)
print(f"Tạo được {top_k.shape[0]} recommendations")
print(top_k.head())

# Đánh giá mô hình
eval_map = map_at_k(test, top_k, k=10)
eval_ndcg = ndcg_at_k(test, top_k, k=10)
eval_precision = precision_at_k(test, top_k, k=10)
eval_recall = recall_at_k(test, top_k, k=10)

print(f"MAP@10: {eval_map:.4f}")
print(f"nDCG@10: {eval_ndcg:.4f}")
print(f"Precision@10: {eval_precision:.4f}")
print(f"Recall@10: {eval_recall:.4f}")

print("\n" + "="*50 + "\n")

# 2. VÍ DỤ VỚI ALS (ALTERNATING LEAST SQUARES) - SỬ DỤNG SPARK
print("=== Ví dụ 2: Sử dụng thuật toán ALS với Spark ===")

try:
    from recommenders.models.als import ALSWrap
    from recommenders.datasets.spark_splitters import spark_random_split
    from recommenders.utils.spark_utils import start_or_get_spark
    
    # Khởi tạo Spark session
    spark = start_or_get_spark("ALS Example")
    
    # Tải dữ liệu dưới dạng Spark DataFrame
    data_spark = movielens.load_spark_df(spark, size='100k')
    
    # Chia dữ liệu
    train_spark, test_spark = spark_random_split(data_spark, ratio=0.8, seed=SEED)
    
    # Khởi tạo mô hình ALS
    als = ALSWrap(
        rank=10,
        maxIter=15,
        regParam=0.05,
        alpha=20,
        coldStartStrategy="drop",
        implicitPrefs=True
    )
    
    # Huấn luyện mô hình
    with Timer() as t:
        model_als = als.fit(train_spark)
    print(f"Thời gian huấn luyện ALS: {t.interval:.2f} giây")
    
    # Tạo dự đoán
    predictions = model_als.transform(test_spark)
    predictions.show(5)
    
    # Đánh giá mô hình (cần chuyển đổi về pandas để đánh giá)
    predictions_pd = predictions.select("UserID", "ItemID", "prediction").toPandas()
    print(f"Tạo được {predictions_pd.shape[0]} predictions")
    
except ImportError:
    print("Spark không được cài đặt. Để sử dụng ALS, cần cài đặt: pip install recommenders[spark]")

print("\n" + "="*50 + "\n")

# 3. VÍ DỤ VỚI NEURAL COLLABORATIVE FILTERING (NCF)
print("=== Ví dụ 3: Sử dụng Neural Collaborative Filtering ===")

try:
    from recommenders.models.ncf.ncf_singlenode import NCF
    from recommenders.models.ncf.dataset import Dataset as NCFDataset
    
    # Chuẩn bị dữ liệu cho NCF
    data_ncf = movielens.load_pandas_df(size='100k')
    
    # Tạo dataset NCF
    dataset = NCFDataset(
        train=train,
        test=test,
        user_col='UserID',
        item_col='ItemID', 
        rating_col='Rating'
    )
    
    # Khởi tạo mô hình NCF
    model_ncf = NCF(
        n_users=dataset.n_users,
        n_items=dataset.n_items,
        model_type="GMF",  # General Matrix Factorization
        n_factors=8,
        layer_sizes=[64, 32, 16, 8],
        n_epochs=50,
        batch_size=256,
        learning_rate=0.001,
        verbose=1,
        seed=SEED
    )
    
    print("Mô hình NCF đã được khởi tạo thành công")
    # Lưu ý: Để huấn luyện NCF cần GPU và TensorFlow/PyTorch
    
except ImportError:
    print("NCF cần các dependencies như TensorFlow. Cài đặt: pip install recommenders[gpu]")

print("\n" + "="*50 + "\n")

# 4. VÍ DỤ TẠO RECOMMENDATION CHO USER CỤ THỂ
print("=== Ví dụ 4: Tạo recommendation cho user cụ thể ===")

# Sử dụng mô hình SAR đã được huấn luyện ở trên
user_id = 1
user_recommendations = model.recommend_k_items(
    pd.DataFrame({'UserID': [user_id]}),
    top_k=5,
    remove_seen=True
)

print(f"Top 5 recommendations cho User {user_id}:")
print(user_recommendations)

# Lấy thông tin về các items được recommend
if not user_recommendations.empty:
    recommended_items = user_recommendations['ItemID'].tolist()
    
    # Có thể join với metadata để lấy thông tin phim
    # (cần tải MovieLens metadata riêng)
    print(f"Recommended Item IDs: {recommended_items}")

print("\n" + "="*50 + "\n")

# 5. VÍ DỤ ĐÁNH GIÁ VÀ SO SÁNH NHIỀU MÔ HÌNH
print("=== Ví dụ 5: So sánh hiệu suất các mô hình ===")

# Tạo dictionary để lưu kết quả
results = {}

# SAR results (đã tính ở trên)
results['SAR'] = {
    'MAP@10': eval_map,
    'nDCG@10': eval_ndcg, 
    'Precision@10': eval_precision,
    'Recall@10': eval_recall
}

# Có thể thêm các mô hình khác như BiVAE, BPR, etc.
try:
    # Ví dụ với mô hình SVD từ Surprise
    from recommenders.models.surprise.surprise_utils import compute_ranking_predictions, predict
    from surprise import SVD, Dataset, Reader
    from surprise.model_selection import train_test_split as surprise_split
    
    # Chuẩn bị dữ liệu cho Surprise
    reader = Reader(rating_scale=(1, 5))
    surprise_data = Dataset.load_from_df(train[['UserID', 'ItemID', 'Rating']], reader)
    
    # Huấn luyện SVD
    svd = SVD(random_state=SEED, n_factors=200, n_epochs=30)
    trainset = surprise_data.build_full_trainset()
    svd.fit(trainset)
    
    # Tạo predictions cho test set
    svd_predictions = predict(svd, test, usercol='UserID', itemcol='ItemID')
    svd_top_k = compute_ranking_predictions(svd_predictions, k=10, threshold=3.5)
    
    # Đánh giá SVD
    svd_map = map_at_k(test, svd_top_k, k=10)
    svd_ndcg = ndcg_at_k(test, svd_top_k, k=10)
    svd_precision = precision_at_k(test, svd_top_k, k=10)
    svd_recall = recall_at_k(test, svd_top_k, k=10)
    
    results['SVD'] = {
        'MAP@10': svd_map,
        'nDCG@10': svd_ndcg,
        'Precision@10': svd_precision,
        'Recall@10': svd_recall
    }
    
except ImportError:
    print("Surprise không được cài đặt. Cài đặt: pip install scikit-surprise")

# In bảng so sánh kết quả
print("Bảng so sánh hiệu suất các mô hình:")
print("-" * 60)
print(f"{'Model':<10} {'MAP@10':<10} {'nDCG@10':<10} {'Precision@10':<12} {'Recall@10':<10}")
print("-" * 60)

for model_name, metrics in results.items():
    print(f"{model_name:<10} {metrics['MAP@10']:<10.4f} {metrics['nDCG@10']:<10.4f} {metrics['Precision@10']:<12.4f} {metrics['Recall@10']:<10.4f}")

print("\n" + "="*50)
print("HOÀN THÀNH! Các ví dụ trên minh họa:")
print("1. Cách sử dụng SAR - một thuật toán collaborative filtering mạnh")
print("2. Cách tích hợp với Spark cho big data (ALS)")
print("3. Cách sử dụng deep learning models (NCF)")
print("4. Cách tạo recommendations cho users cụ thể")
print("5. Cách đánh giá và so sánh hiệu suất mô hình")
print("\nTham khảo thêm tại: https://github.com/recommenders-team/recommenders")
