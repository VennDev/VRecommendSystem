# VRecommendSystem - Cấu trúc thư mục được tối ưu hóa

```
VRecommendSystem/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── Makefile
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── logging.conf
│   ├── database.py
│   └── environments/
│       ├── development.yaml
│       ├── staging.yaml
│       └── production.yaml
│
├── src/
│   └── vrecommend/
│       ├── __init__.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── exceptions.py
│       │   ├── types.py
│       │   └── utils.py
│       │
│       ├── data/
│       │   ├── __init__.py
│       │   ├── schemas/
│       │   │   ├── __init__.py
│       │   │   ├── user.py
│       │   │   ├── item.py
│       │   │   └── interaction.py
│       │   ├── collectors/
│       │   │   ├── __init__.py
│       │   │   ├── base_collector.py
│       │   │   ├── api_collector.py
│       │   │   ├── database_collector.py
│       │   │   └── stream_collector.py
│       │   ├── processors/
│       │   │   ├── __init__.py
│       │   │   ├── feature_processor.py
│       │   │   ├── data_cleaner.py
│       │   │   └── data_validator.py
│       │   └── storages/
│       │       ├── __init__.py
│       │       ├── database.py
│       │       ├── cache.py
│       │       └── file_storage.py
│       │
│       ├── features/
│       │   ├── __init__.py
│       │   ├── extractors/
│       │   │   ├── __init__.py
│       │   │   ├── user_features.py
│       │   │   ├── item_features.py
│       │   │   ├── interaction_features.py
│       │   │   └── contextual_features.py
│       │   ├── transformers/
│       │   │   ├── __init__.py
│       │   │   ├── text_transformer.py
│       │   │   ├── numerical_transformer.py
│       │   │   └── categorical_transformer.py
│       │   └── store/
│       │       ├── __init__.py
│       │       ├── feature_store.py
│       │       └── feature_registry.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base/
│       │   │   ├── __init__.py
│       │   │   ├── base_model.py
│       │   │   └── model_interface.py
│       │   ├── collaborative/
│       │   │   ├── __init__.py
│       │   │   ├── matrix_factorization.py
│       │   │   ├── neural_cf.py
│       │   │   └── als.py
│       │   ├── content_based/
│       │   │   ├── __init__.py
│       │   │   ├── tfidf_model.py
│       │   │   ├── embedding_model.py
│       │   │   └── similarity_model.py
│       │   ├── deep_learning/
│       │   │   ├── __init__.py
│       │   │   ├── wide_deep.py
│       │   │   ├── deepfm.py
│       │   │   ├── neural_mf.py
│       │   │   └── autoint.py
│       │   ├── graph/
│       │   │   ├── __init__.py
│       │   │   ├── graph_sage.py
│       │   │   ├── gat.py
│       │   │   └── lightgcn.py
│       │   ├── ensemble/
│       │   │   ├── __init__.py
│       │   │   ├── hybrid_model.py
│       │   │   ├── stacking.py
│       │   │   └── blending.py
│       │   └── bandit/
│       │       ├── __init__.py
│       │       ├── contextual_bandit.py
│       │       ├── multi_armed_bandit.py
│       │       └── thompson_sampling.py
│       │
│       ├── training/
│       │   ├── __init__.py
│       │   ├── trainer.py
│       │   ├── pipeline.py
│       │   ├── hyperparameter_tuning.py
│       │   ├── model_selection.py
│       │   └── callbacks/
│       │       ├── __init__.py
│       │       ├── early_stopping.py
│       │       ├── model_checkpoint.py
│       │       └── metrics_logger.py
│       │
│       ├── serving/
│       │   ├── __init__.py
│       │   ├── predictor.py
│       │   ├── batch_predictor.py
│       │   ├── real_time_predictor.py
│       │   ├── model_loader.py
│       │   └── post_processors/
│       │       ├── __init__.py
│       │       ├── diversity_filter.py
│       │       ├── business_rules.py
│       │       └── ranking_optimizer.py
│       │
│       ├── evaluation/
│       │   ├── __init__.py
│       │   ├── metrics/
│       │   │   ├── __init__.py
│       │   │   ├── ranking_metrics.py
│       │   │   ├── rating_metrics.py
│       │   │   ├── diversity_metrics.py
│       │   │   └── business_metrics.py
│       │   ├── evaluator.py
│       │   ├── cross_validator.py
│       │   └── ab_testing.py
│       │
│       ├── monitoring/
│       │   ├── __init__.py
│       │   ├── metrics_collector.py
│       │   ├── performance_monitor.py
│       │   ├── data_drift_detector.py
│       │   ├── model_monitor.py
│       │   └── alerting.py
│       │
│       └── utils/
│           ├── __init__.py
│           ├── logging.py
│           ├── decorators.py
│           ├── validators.py
│           ├── serializers.py
│           └── helpers.py
│
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── dependencies.py
│   ├── middleware.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── recommendations.py
│   │   ├── users.py
│   │   ├── items.py
│   │   ├── interactions.py
│   │   ├── models.py
│   │   └── health.py
│   └── schemas/
│       ├── __init__.py
│       ├── request.py
│       ├── response.py
│       └── common.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_core/
│   │   ├── test_data/
│   │   ├── test_features/
│   │   ├── test_models/
│   │   ├── test_training/
│   │   ├── test_serving/
│   │   ├── test_evaluation/
│   │   ├── test_monitoring/
│   │   └── test_utils/
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api/
│   │   ├── test_pipeline/
│   │   └── test_serving/
│   └── e2e/
│       ├── __init__.py
│       └── test_recommendation_flow.py
│
├── scripts/
│   ├── setup.sh
│   ├── train_model.py
│   ├── batch_inference.py
│   ├── data_migration.py
│   ├── model_deployment.py
│   └── monitoring_setup.py
│
├── notebooks/
│   ├── data_exploration.ipynb
│   ├── model_experiments.ipynb
│   ├── feature_analysis.ipynb
│   └── performance_analysis.ipynb
│
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── api_documentation.md
│   ├── model_documentation.md
│   ├── deployment_guide.md
│   └── troubleshooting.md
│
├── deployments/
│   ├── docker/
│   │   ├── api.Dockerfile
│   │   ├── training.Dockerfile
│   │   ├── batch.Dockerfile
│   │   └── docker-compose.yml
│   ├── kubernetes/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── storage/
│   ├── data/
│   │   ├── raw/
│   │   ├── processed/
│   │   ├── features/
│   │   └── experiments/
│   ├── models/
│   │   ├── checkpoints/
│   │   ├── artifacts/
│   │   └── registry/
│   └── logs/
│       ├── application/
│       ├── training/
│       └── serving/
│
└── .github/
    └── workflows/
        ├── ci.yml
        ├── cd.yml
        └── security.yml
```

## Những thay đổi chính:

### 1. Tách API ra khỏi src/

- API được tách thành module riêng ở cấp cao nhất để dễ deploy và scale

### 2. Gom nhóm storage/

- Tất cả dữ liệu, model, logs được gom vào thư mục `storage/` để dễ quản lý và backup

### 3. Sắp xếp lại data/

- Schemas được đặt trước để định nghĩa cấu trúc dữ liệu
- Collectors, processors, storages được sắp xếp theo luồng xử lý

### 4. Tối ưu deployments/

- Docker compose được chuyển vào deployments/docker/
- Các file deployment được nhóm theo công nghệ

### 5. Thêm .github/workflows/

- Hỗ trợ CI/CD với GitHub Actions

### 6. Cải thiện tests/

- Thêm test_core/ để test các module cơ bản
- Sắp xếp lại theo cấu trúc src/

## Lợi ích của cấu trúc mới:

1. **Tách biệt concerns**: API, core logic, deployment tách riêng
2. **Dễ scale**: API có thể deploy độc lập
3. **Quản lý storage tốt hơn**: Tất cả dữ liệu ở một nơi
4. **DevOps friendly**: Deployment configs được tổ chức rõ ràng
5. **Testing structure**: Tests được sắp xếp theo module và cấp độ
