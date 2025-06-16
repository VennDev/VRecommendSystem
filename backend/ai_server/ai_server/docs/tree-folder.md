VRecommendSystem/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── Makefile
│
├── config/
│ ├── **init**.py
│ ├── settings.py
│ ├── logging.conf
│ ├── database.py
│ └── environments/
│ ├── development.yaml
│ ├── staging.yaml
│ └── production.yaml
│
├── src/
│ └── vrecommend/
│ ├── **init**.py
│ ├── core/
│ │ ├── **init**.py
│ │ ├── base.py
│ │ ├── exceptions.py
│ │ ├── types.py
│ │ └── utils.py
│ │
│ ├── data/
│ │ ├── **init**.py
│ │ ├── collectors/
│ │ │ ├── **init**.py
│ │ │ ├── base_collector.py
│ │ │ ├── api_collector.py
│ │ │ ├── database_collector.py
│ │ │ └── stream_collector.py
│ │ ├── processors/
│ │ │ ├── **init**.py
│ │ │ ├── feature_processor.py
│ │ │ ├── data_cleaner.py
│ │ │ └── data_validator.py
│ │ ├── storages/
│ │ │ ├── **init**.py
│ │ │ ├── database.py
│ │ │ ├── cache.py
│ │ │ └── file_storage.py
│ │ └── schemas/
│ │ ├── **init**.py
│ │ ├── user.py
│ │ ├── item.py
│ │ └── interaction.py
│ │
│ ├── features/
│ │ ├── **init**.py
│ │ ├── extractors/
│ │ │ ├── **init**.py
│ │ │ ├── user_features.py
│ │ │ ├── item_features.py
│ │ │ ├── interaction_features.py
│ │ │ └── contextual_features.py
│ │ ├── transformers/
│ │ │ ├── **init**.py
│ │ │ ├── text_transformer.py
│ │ │ ├── numerical_transformer.py
│ │ │ └── categorical_transformer.py
│ │ └── store/
│ │ ├── **init**.py
│ │ ├── feature_store.py
│ │ └── feature_registry.py
│ │
│ ├── models/
│ │ ├── **init**.py
│ │ ├── base/
│ │ │ ├── **init**.py
│ │ │ ├── base_model.py
│ │ │ └── model_interface.py
│ │ ├── collaborative/
│ │ │ ├── **init**.py
│ │ │ ├── matrix_factorization.py
│ │ │ ├── neural_cf.py
│ │ │ └── als.py
│ │ ├── content_based/
│ │ │ ├── **init**.py
│ │ │ ├── tfidf_model.py
│ │ │ ├── embedding_model.py
│ │ │ └── similarity_model.py
│ │ ├── deep_learning/
│ │ │ ├── **init**.py
│ │ │ ├── wide_deep.py
│ │ │ ├── deepfm.py
│ │ │ ├── neural_mf.py
│ │ │ └── autoint.py
│ │ ├── graph/
│ │ │ ├── **init**.py
│ │ │ ├── graph_sage.py
│ │ │ ├── gat.py
│ │ │ └── lightgcn.py
│ │ ├── ensemble/
│ │ │ ├── **init**.py
│ │ │ ├── hybrid_model.py
│ │ │ ├── stacking.py
│ │ │ └── blending.py
│ │ └── bandit/
│ │ ├── **init**.py
│ │ ├── contextual_bandit.py
│ │ ├── multi_armed_bandit.py
│ │ └── thompson_sampling.py
│ │
│ ├── training/
│ │ ├── **init**.py
│ │ ├── trainer.py
│ │ ├── pipeline.py
│ │ ├── hyperparameter_tuning.py
│ │ ├── model_selection.py
│ │ └── callbacks/
│ │ ├── **init**.py
│ │ ├── early_stopping.py
│ │ ├── model_checkpoint.py
│ │ └── metrics_logger.py
│ │
│ ├── serving/
│ │ ├── **init**.py
│ │ ├── predictor.py
│ │ ├── batch_predictor.py
│ │ ├── real_time_predictor.py
│ │ ├── model_loader.py
│ │ └── post_processors/
│ │ ├── **init**.py
│ │ ├── diversity_filter.py
│ │ ├── business_rules.py
│ │ └── ranking_optimizer.py
│ │
│ ├── evaluation/
│ │ ├── **init**.py
│ │ ├── metrics/
│ │ │ ├── **init**.py
│ │ │ ├── ranking_metrics.py
│ │ │ ├── rating_metrics.py
│ │ │ ├── diversity_metrics.py
│ │ │ └── business_metrics.py
│ │ ├── evaluator.py
│ │ ├── cross_validator.py
│ │ └── ab_testing.py
│ │
│ ├── api/
│ │ ├── **init**.py
│ │ ├── main.py
│ │ ├── dependencies.py
│ │ ├── middleware.py
│ │ ├── routers/
│ │ │ ├── **init**.py
│ │ │ ├── recommendations.py
│ │ │ ├── users.py
│ │ │ ├── items.py
│ │ │ ├── interactions.py
│ │ │ ├── models.py
│ │ │ └── health.py
│ │ └── schemas/
│ │ ├── **init**.py
│ │ ├── request.py
│ │ ├── response.py
│ │ └── common.py
│ │
│ ├── monitoring/
│ │ ├── **init**.py
│ │ ├── metrics_collector.py
│ │ ├── performance_monitor.py
│ │ ├── data_drift_detector.py
│ │ ├── model_monitor.py
│ │ └── alerting.py
│ │
│ └── utils/
│ ├── **init**.py
│ ├── logging.py
│ ├── decorators.py
│ ├── validators.py
│ ├── serializers.py
│ └── helpers.py
│
├── tests/
│ ├── **init**.py
│ ├── conftest.py
│ ├── unit/
│ │ ├── **init**.py
│ │ ├── test_models/
│ │ ├── test_features/
│ │ ├── test_data/
│ │ └── test_utils/
│ ├── integration/
│ │ ├── **init**.py
│ │ ├── test_api/
│ │ ├── test_pipeline/
│ │ └── test_serving/
│ └── e2e/
│ ├── **init**.py
│ └── test_recommendation_flow.py
│
├── scripts/
│ ├── setup.sh
│ ├── train_model.py
│ ├── batch_inference.py
│ ├── data_migration.py
│ ├── model_deployment.py
│ └── monitoring_setup.py
│
├── notebooks/
│ ├── data_exploration.ipynb
│ ├── model_experiments.ipynb
│ ├── feature_analysis.ipynb
│ └── performance_analysis.ipynb
│
├── docs/
│ ├── README.md
│ ├── architecture.md
│ ├── api_documentation.md
│ ├── model_documentation.md
│ ├── deployment_guide.md
│ └── troubleshooting.md
│
├── deployments/
│ ├── kubernetes/
│ │ ├── namespace.yaml
│ │ ├── configmap.yaml
│ │ ├── deployment.yaml
│ │ ├── service.yaml
│ │ └── ingress.yaml
│ ├── docker/
│ │ ├── api.Dockerfile
│ │ ├── training.Dockerfile
│ │ └── batch.Dockerfile
│ └── terraform/
│ ├── main.tf
│ ├── variables.tf
│ └── outputs.tf
│
├── data/
│ ├── raw/
│ ├── processed/
│ ├── features/
│ ├── models/
│ └── experiments/
│
├── models/
│ ├── checkpoints/
│ ├── artifacts/
│ └── registry/
│
└── logs/
├── application/
├── training/
└── serving/
