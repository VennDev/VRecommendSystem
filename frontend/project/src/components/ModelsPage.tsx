import { Cpu, Eye, Play, Plus, Trash2, Settings, Save } from "lucide-react";
import React, { useEffect, useState } from "react";
import { apiService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { activityLogger } from "../services/activityLogger";
import { ConfirmDialog } from "./common/ConfirmDialog";

interface Model {
  model_id: string;
  model_name: string;
  algorithm: string;
  model_type: string;
  status: string;
  created_at: string;
  training_completed_at?: string;
  hyperparameters?: Record<string, any>;
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

interface AlgorithmInfo {
  algorithm: string;
  model_type: string;
  default_params: Record<string, any>;
  description: string;
  use_case: string;
}

const ModelsPage: React.FC = () => {
  const { user } = useAuth();
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [algorithms, setAlgorithms] = useState<Record<string, AlgorithmInfo>>({});

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showEditHyperparametersModal, setShowEditHyperparametersModal] = useState(false);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [formData, setFormData] = useState({
    modelId: "",
    modelName: "",
    algorithm: "nmf",
    message: "",
    hyperparameters: {} as Record<string, any>,
  });
  const [isCreating, setIsCreating] = useState(false);
  const [isSavingHyperparameters, setIsSavingHyperparameters] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    modelId: string;
    modelName: string;
  }>({
    isOpen: false,
    modelId: "",
    modelName: "",
  });

  useEffect(() => {
    fetchModels();
    fetchAlgorithms();

    const interval = setInterval(() => {
      fetchModels();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const fetchAlgorithms = async () => {
    try {
      const response = await apiService.getAvailableAlgorithms();
      if (response.data?.algorithms) {
        setAlgorithms(response.data.algorithms);
      }
    } catch (error) {
      console.error("Failed to fetch algorithms:", error);
    }
  };

  const fetchModels = async () => {
    try {
      const response = await apiService.listModels();
      if (response.data) {
        setModels(Object.values(response.data));
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
        formData.message,
        Object.keys(formData.hyperparameters).length > 0
          ? formData.hyperparameters
          : undefined
      );

      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Model created successfully!");

        if (user) {
          await activityLogger.log(user.id, user.email, {
            action: "create",
            resourceType: "model",
            resourceId: formData.modelId,
            details: {
              model_name: formData.modelName,
              algorithm: formData.algorithm,
            },
          });
        }

        setShowCreateModal(false);
        setFormData({
          modelId: "",
          modelName: "",
          algorithm: "nmf",
          message: "",
          hyperparameters: {},
        });
        fetchModels();
      }
    } catch (error) {
      alert("Failed to create model");
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteModelConfirm = (modelId: string) => {
    setConfirmDialog({
      isOpen: true,
      modelId: modelId,
      modelName: modelId,
    });
  };

  const handleDeleteModel = async () => {
    const modelId = confirmDialog.modelId;
    if (!modelId) return;

    try {
      const response = await apiService.deleteModel(modelId);
      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Model deleted successfully!");

        if (user) {
          await activityLogger.log(user.id, user.email, {
            action: "delete",
            resourceType: "model",
            resourceId: modelId,
            details: {},
          });
        }

        fetchModels();
      }
    } catch (error) {
      alert("Failed to delete model");
    }
  };

  const handleViewDetails = async (model: Model) => {
    try {
      const response = await apiService.getModelInfo(model.model_id);
      if (response.data) {
        setSelectedModel(response.data);
        setShowDetailsModal(true);
      }
    } catch (error) {
      console.error("Failed to fetch model details:", error);
      setSelectedModel(model);
      setShowDetailsModal(true);
    }
  };

  const handleEditHyperparameters = async (model: Model) => {
    try {
      const response = await apiService.getModelInfo(model.model_id);
      if (response.data) {
        setSelectedModel(response.data);
        setFormData({
          ...formData,
          hyperparameters: response.data.hyperparameters || {},
        });
        setShowEditHyperparametersModal(true);
      }
    } catch (error) {
      console.error("Failed to fetch model details:", error);
      alert("Failed to load model hyperparameters");
    }
  };

  const handleSaveHyperparameters = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModel) return;

    setIsSavingHyperparameters(true);
    try {
      const response = await apiService.updateModelHyperparameters(
        selectedModel.model_id,
        formData.hyperparameters
      );

      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Hyperparameters updated successfully! Model needs to be retrained.");

        if (user) {
          await activityLogger.log(user.id, user.email, {
            action: "update_hyperparameters",
            resourceType: "model",
            resourceId: selectedModel.model_id,
            details: {
              hyperparameters: formData.hyperparameters,
            },
          });
        }

        setShowEditHyperparametersModal(false);
        fetchModels();
      }
    } catch (error) {
      alert("Failed to update hyperparameters");
    } finally {
      setIsSavingHyperparameters(false);
    }
  };

  const handleHyperparameterChange = (key: string, value: any) => {
    setFormData({
      ...formData,
      hyperparameters: {
        ...formData.hyperparameters,
        [key]: value,
      },
    });
  };

  const handleAlgorithmChange = (algorithm: string) => {
    const algorithmInfo = algorithms[algorithm];
    if (algorithmInfo) {
      setFormData({
        ...formData,
        algorithm,
        hyperparameters: { ...algorithmInfo.default_params },
      });
    } else {
      setFormData({
        ...formData,
        algorithm,
        hyperparameters: {},
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "completed":
        return "badge-success";
      case "training":
      case "initializing":
        return "badge-warning";
      case "failed":
      case "stopped":
        return "badge-error";
      case "modified":
      case "validating":
        return "badge-info";
      default:
        return "badge-ghost";
    }
  };

  const formatAlgorithmName = (algorithm: string) => {
    return algorithm.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const renderHyperparameterInput = (key: string, value: any) => {
    if (typeof value === "boolean") {
      return (
        <input
          type="checkbox"
          checked={value}
          onChange={(e) => handleHyperparameterChange(key, e.target.checked)}
          className="checkbox checkbox-primary"
        />
      );
    } else if (typeof value === "number") {
      return (
        <input
          type="number"
          value={value}
          onChange={(e) => handleHyperparameterChange(key, parseFloat(e.target.value))}
          className="input input-bordered input-sm w-full"
          step="any"
        />
      );
    } else if (typeof value === "string") {
      return (
        <input
          type="text"
          value={value}
          onChange={(e) => handleHyperparameterChange(key, e.target.value)}
          className="input input-bordered input-sm w-full"
        />
      );
    } else {
      return (
        <input
          type="text"
          value={JSON.stringify(value)}
          onChange={(e) => {
            try {
              handleHyperparameterChange(key, JSON.parse(e.target.value));
            } catch {
              handleHyperparameterChange(key, e.target.value);
            }
          }}
          className="input input-bordered input-sm w-full font-mono text-xs"
        />
      );
    }
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
            Manage and monitor your AI models <span className="text-xs text-base-content/50">(Auto-refreshes every 5s)</span>
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
        {models.map((model) => (
          <div
            key={model.model_id}
            className="card bg-base-100 shadow-sm hover:shadow-md transition-shadow duration-200"
          >
            <div className="card-body">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-primary/10 p-2 rounded-lg">
                  <Cpu className="h-6 w-6 text-primary" />
                </div>
                <div className="flex items-center gap-2">
                  {model.status === 'training' && (
                    <span className="loading loading-spinner loading-xs"></span>
                  )}
                  <div className={`badge ${getStatusColor(model.status)}`}>
                    {model.status}
                  </div>
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

              <div className="card-actions justify-end flex-wrap gap-2">
                <button
                  onClick={() => handleViewDetails(model)}
                  className="btn btn-info btn-sm gap-1"
                >
                  <Eye className="h-4 w-4" />
                  <span>Details</span>
                </button>
                <button
                  onClick={() => handleEditHyperparameters(model)}
                  className="btn btn-secondary btn-sm gap-1"
                >
                  <Settings className="h-4 w-4" />
                  <span>Settings</span>
                </button>
                <button
                  onClick={() => handleDeleteModelConfirm(model.model_id)}
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

      {/* Edit Hyperparameters Modal */}
      {showEditHyperparametersModal && selectedModel && (
        <div className="modal modal-open">
          <div className="modal-box max-w-2xl">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Edit Hyperparameters: {selectedModel.model_name}
            </h2>

            <form onSubmit={handleSaveHyperparameters} className="space-y-4">
              <div className="alert alert-info">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <span className="text-sm">
                  After updating hyperparameters, the model will need to be retrained.
                </span>
              </div>

              <div className="max-h-96 overflow-y-auto space-y-3">
                {Object.entries(formData.hyperparameters).map(([key, value]) => (
                  <div key={key} className="form-control">
                    <label className="label">
                      <span className="label-text font-semibold">{key}</span>
                      <span className="label-text-alt text-xs">
                        {typeof value}
                      </span>
                    </label>
                    {renderHyperparameterInput(key, value)}
                  </div>
                ))}
              </div>

              <div className="modal-action">
                <button
                  type="submit"
                  disabled={isSavingHyperparameters}
                  className="btn btn-primary gap-2"
                >
                  <Save className="h-4 w-4" />
                  {isSavingHyperparameters ? "Saving..." : "Save Changes"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowEditHyperparametersModal(false)}
                  className="btn btn-ghost"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Model Details Modal */}
      {showDetailsModal && selectedModel && (
        <div className="modal modal-open">
          <div className="modal-box max-w-3xl">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Model Details: {selectedModel.model_name}
            </h2>

            <div className="space-y-4 max-h-96 overflow-y-auto">
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

              {selectedModel.hyperparameters && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">Hyperparameters</span>
                  </label>
                  <div className="bg-base-200 p-4 rounded-lg">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {Object.entries(selectedModel.hyperparameters).map(([key, value]) => (
                        <div key={key}>
                          <span className="font-semibold">{key}:</span> {JSON.stringify(value)}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

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
          <div className="modal-box max-w-2xl">
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
                  onChange={(e) => handleAlgorithmChange(e.target.value)}
                  className="select select-bordered w-full"
                >
                  {Object.keys(algorithms).map((algo) => (
                    <option key={algo} value={algo}>
                      {formatAlgorithmName(algo)}
                    </option>
                  ))}
                </select>
                {algorithms[formData.algorithm] && (
                  <p className="text-xs text-base-content/60 mt-1">
                    {algorithms[formData.algorithm].description}
                  </p>
                )}
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

              {/* Hyperparameters Section */}
              {Object.keys(formData.hyperparameters).length > 0 && (
                <div>
                  <label className="label">
                    <span className="label-text font-semibold">Hyperparameters</span>
                  </label>
                  <div className="bg-base-200 p-4 rounded-lg max-h-60 overflow-y-auto space-y-3">
                    {Object.entries(formData.hyperparameters).map(([key, value]) => (
                      <div key={key} className="form-control">
                        <label className="label">
                          <span className="label-text text-sm">{key}</span>
                          <span className="label-text-alt text-xs">
                            {typeof value}
                          </span>
                        </label>
                        {renderHyperparameterInput(key, value)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

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

      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        onClose={() => setConfirmDialog({ isOpen: false, modelId: "", modelName: "" })}
        onConfirm={handleDeleteModel}
        title="Confirm Delete"
        message={`Are you sure you want to delete model "${confirmDialog.modelId}"? This action cannot be undone.`}
        type="delete"
        confirmText="Delete"
        cancelText="Cancel"
      />
    </div>
  );
};

export default ModelsPage;
