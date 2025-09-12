import { Cpu, Eye, Play, Plus, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { apiService } from "../services/api";

interface Model {
  model_id: string;
  model_name: string;
  algorithm: string;
  model_type: string;
  status: string;
  created_at: string;
  training_completed_at?: string;
  model_metrics?: {
    training_time: number;
    n_users: number;
    n_items: number;
    n_interactions: number;
    sparsity: number;
  };
  final_stats?: {
    total_interactions: number;
    unique_users: number;
    unique_items: number;
    has_user_features: boolean;
    has_item_features: boolean;
  };
}

const ModelsPage: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [formData, setFormData] = useState({
    modelId: "",
    modelName: "",
    algorithm: "nmf",
    message: "",
  });
  const [isCreating, setIsCreating] = useState(false);

  const algorithms = [
    "nmf",
    "nmf_fast",
    "nmf_accurate",
    "svd",
    "svd_fast",
    "svd_accurate",
    "hybrid_nmf",
  ];

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await apiService.listModels();
      if (response.data) {
        setModels(response.data);
      }
    } catch (error) {
      console.error("Failed to fetch models:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateModel = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);

    try {
      const response = await apiService.createModel(
        formData.modelId,
        formData.modelName,
        formData.algorithm,
        formData.message
      );

      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Model created successfully!");
        setShowCreateModal(false);
        setFormData({
          modelId: "",
          modelName: "",
          algorithm: "nmf",
          message: "",
        });
        fetchModels();
      }
    } catch (error) {
      alert("Failed to create model");
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteModel = async (modelId: string) => {
    if (window.confirm(`Are you sure you want to delete model "${modelId}"?`)) {
      try {
        const response = await apiService.deleteModel(modelId);
        if (response.error) {
          alert("Error: " + response.error);
        } else {
          alert("Model deleted successfully!");
          fetchModels();
        }
      } catch (error) {
        alert("Failed to delete model");
      }
    }
  };

  const handleViewDetails = (model: Model) => {
    setSelectedModel(model);
    setShowDetailsModal(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "badge-success";
      case "training":
        return "badge-warning";
      case "failed":
        return "badge-error";
      default:
        return "badge-ghost";
    }
  };

  const formatAlgorithmName = (algorithm: string) => {
    return algorithm.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="loading loading-spinner loading-lg"></div>
          <p className="text-base-content/70 mt-4">Loading models...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-base-content mb-2">
            AI Models
          </h1>
          <p className="text-base-content/70">
            Manage and monitor your AI models
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary gap-2"
        >
          <Plus className="h-5 w-5" />
          <span>Create Model</span>
        </button>
      </div>

      {/* Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.values(models).map((model) => (
          <div
            key={model.model_id}
            className="card bg-base-100 shadow-sm hover:shadow-md transition-shadow duration-200"
          >
            <div className="card-body">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-primary/10 p-2 rounded-lg">
                  <Cpu className="h-6 w-6 text-primary" />
                </div>
                <div className={`badge ${getStatusColor(model.status)}`}>
                  {model.status}
                </div>
              </div>

              <h3 className="card-title text-base-content mb-2">
                {model.model_name}
              </h3>
              <p className="text-sm text-base-content/70 mb-2">
                Algorithm: {formatAlgorithmName(model.algorithm)}
              </p>
              <p className="text-sm text-base-content/70 mb-2">
                Type: {model.model_type?.toUpperCase() || "Unknown"}
              </p>
              <p className="text-xs text-base-content/50 mb-4">
                Created: {new Date(model.created_at).toLocaleDateString()}
              </p>

              {model.model_metrics && (
                <div className="text-xs text-base-content/60 mb-4 space-y-1">
                  <div>Users: {model.model_metrics.n_users}</div>
                  <div>Items: {model.model_metrics.n_items}</div>
                  <div>Interactions: {model.model_metrics.n_interactions}</div>
                </div>
              )}

              <div className="card-actions justify-end">
                <button
                  onClick={() => handleViewDetails(model)}
                  className="btn btn-info btn-sm gap-1"
                >
                  <Eye className="h-4 w-4" />
                  <span>Details</span>
                </button>
                <button className="btn btn-primary btn-sm gap-1">
                  <Play className="h-4 w-4" />
                  <span>Train</span>
                </button>
                <button
                  onClick={() => handleDeleteModel(model.model_id)}
                  className="btn btn-error btn-sm"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {models.length === 0 && (
        <div className="text-center py-12">
          <Cpu className="h-12 w-12 text-base-content/40 mx-auto mb-4" />
          <p className="text-base-content/70 text-lg">No models found</p>
          <p className="text-base-content/50 text-sm">
            Create your first model to get started
          </p>
        </div>
      )}

      {/* Model Details Modal */}
      {showDetailsModal && selectedModel && (
        <div className="modal modal-open">
          <div className="modal-box max-w-2xl">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Model Details: {selectedModel.model_name}
            </h2>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">Model ID</span>
                  </label>
                  <p className="text-base-content">{selectedModel.model_id}</p>
                </div>
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">Status</span>
                  </label>
                  <div
                    className={`badge ${getStatusColor(selectedModel.status)}`}
                  >
                    {selectedModel.status}
                  </div>
                </div>
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">Algorithm</span>
                  </label>
                  <p className="text-base-content">
                    {formatAlgorithmName(selectedModel.algorithm)}
                  </p>
                </div>
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">Model Type</span>
                  </label>
                  <p className="text-base-content">
                    {selectedModel.model_type?.toUpperCase() || "Unknown"}
                  </p>
                </div>
              </div>

              {selectedModel.model_metrics && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">
                      Training Metrics
                    </span>
                  </label>
                  <div className="bg-base-200 p-4 rounded-lg">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        Training Time:{" "}
                        {selectedModel.model_metrics.training_time.toFixed(3)}s
                      </div>
                      <div>Users: {selectedModel.model_metrics.n_users}</div>
                      <div>Items: {selectedModel.model_metrics.n_items}</div>
                      <div>
                        Interactions:{" "}
                        {selectedModel.model_metrics.n_interactions}
                      </div>
                      <div>
                        Sparsity:{" "}
                        {(selectedModel.model_metrics.sparsity * 100).toFixed(
                          2
                        )}
                        %
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {selectedModel.final_stats && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">
                      Final Statistics
                    </span>
                  </label>
                  <div className="bg-base-200 p-4 rounded-lg">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        Total Interactions:{" "}
                        {selectedModel.final_stats.total_interactions}
                      </div>
                      <div>
                        Unique Users: {selectedModel.final_stats.unique_users}
                      </div>
                      <div>
                        Unique Items: {selectedModel.final_stats.unique_items}
                      </div>
                      <div>
                        Has User Features:{" "}
                        {selectedModel.final_stats.has_user_features
                          ? "Yes"
                          : "No"}
                      </div>
                      <div>
                        Has Item Features:{" "}
                        {selectedModel.final_stats.has_item_features
                          ? "Yes"
                          : "No"}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">Created At</span>
                  </label>
                  <p className="text-base-content text-sm">
                    {new Date(selectedModel.created_at).toLocaleString()}
                  </p>
                </div>
                {selectedModel.training_completed_at && (
                  <div>
                    <label className="label">
                      <span className="label-text font-semibold">
                        Training Completed
                      </span>
                    </label>
                    <p className="text-base-content text-sm">
                      {new Date(
                        selectedModel.training_completed_at
                      ).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div className="modal-action">
              <button
                onClick={() => setShowDetailsModal(false)}
                className="btn btn-ghost"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Create Model Modal */}
      {showCreateModal && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Create New Model
            </h2>
            <form onSubmit={handleCreateModel} className="space-y-4">
              <div>
                <label className="label">
                  <span className="label-text">Model ID</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.modelId}
                  onChange={(e) =>
                    setFormData({ ...formData, modelId: e.target.value })
                  }
                  className="input input-bordered w-full"
                  placeholder="unique_model_id"
                />
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Model Name</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.modelName}
                  onChange={(e) =>
                    setFormData({ ...formData, modelName: e.target.value })
                  }
                  className="input input-bordered w-full"
                  placeholder="My AI Model"
                />
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Algorithm</span>
                </label>
                <select
                  value={formData.algorithm}
                  onChange={(e) =>
                    setFormData({ ...formData, algorithm: e.target.value })
                  }
                  className="select select-bordered w-full"
                >
                  {algorithms.map((algo) => (
                    <option key={algo} value={algo}>
                      {formatAlgorithmName(algo)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Description</span>
                </label>
                <textarea
                  value={formData.message}
                  onChange={(e) =>
                    setFormData({ ...formData, message: e.target.value })
                  }
                  className="textarea textarea-bordered w-full"
                  rows={3}
                  placeholder="Model description..."
                />
              </div>

              <div className="modal-action">
                <button
                  type="submit"
                  disabled={isCreating}
                  className="btn btn-primary"
                >
                  {isCreating ? "Creating..." : "Create Model"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-ghost"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelsPage;
