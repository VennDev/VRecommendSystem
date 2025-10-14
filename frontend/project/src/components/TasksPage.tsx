import { Calendar, Clock, CreditCard as Edit, Plus, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { apiService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { activityLogger } from "../services/activityLogger";

interface Task {
  model_id: string;
  interactions_data_chef_id: string;
  item_features_data_chef_id?: string | null;
  user_features_data_chef_id?: string | null;
  interval: number;
  name?: string;
  status?: "running" | "paused" | "completed";
}

interface Model {
  model_id: string;
  model_name: string;
  algorithm: string;
  model_type: string;
  status: string;
}

interface DataChef {
  id: string;
  name: string;
  type: string;
}

const TasksPage: React.FC = () => {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [dataChefs, setDataChefs] = useState<DataChef[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [formData, setFormData] = useState({
    taskName: "",
    modelId: "",
    dataChefId: "",
    itemFeaturesDataChefId: "",
    userFeaturesDataChefId: "",
    interval: 3600,
  });
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingResources, setLoadingResources] = useState(false);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await apiService.listTasks();
      if (response.data) {
        const tasksObject = response.data;
        const tasksWithNames = Object.entries(tasksObject).map(
          ([task, index]) => ({
            name: task,
            ...index,
          })
        );
        setTasks(tasksWithNames);
      }
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchModelsAndDataChefs = async () => {
    setLoadingResources(true);
    try {
      const [modelsResponse, dataChefsResponse] = await Promise.all([
        apiService.listModels(),
        apiService.listDataChefs(),
      ]);

      if (modelsResponse.data) {
        const modelsArray = Object.values(modelsResponse.data) as Model[];
        setModels(modelsArray);
      }

      if (dataChefsResponse.data) {
        const dataChefsObject = dataChefsResponse.data;
        const dataChefsArray = Object.entries(dataChefsObject).map(
          ([key, value]: [string, any]) => ({
            id: key,
            name: key,
            type: value.type || "unknown",
          })
        );
        setDataChefs(dataChefsArray);
      }
    } catch (error) {
      console.error("Failed to fetch models and data chefs:", error);
    } finally {
      setLoadingResources(false);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);

    try {
      const response = await apiService.addModelTask(
        formData.taskName,
        formData.modelId,
        formData.dataChefId,
        formData.interval
      );

      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Task created successfully!");

        if (user) {
          await activityLogger.log(user.id, user.email, {
            action: "create",
            resourceType: "task",
            resourceId: formData.taskName,
            details: {
              model_id: formData.modelId,
              data_chef_id: formData.dataChefId,
              interval: formData.interval,
            },
          });
        }

        setShowCreateModal(false);
        resetForm();
        fetchTasks();
      }
    } catch (error) {
      alert("Failed to create task");
    } finally {
      setIsCreating(false);
    }
  };

  const handleEditTask = (task: Task) => {
    setSelectedTask(task);
    setFormData({
      taskName: task.name || "",
      modelId: task.model_id,
      dataChefId: task.interactions_data_chef_id,
      itemFeaturesDataChefId: task.item_features_data_chef_id || "",
      userFeaturesDataChefId: task.user_features_data_chef_id || "",
      interval: task.interval,
    });
    fetchModelsAndDataChefs();
    setShowEditModal(true);
  };

  const handleUpdateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask) return;

    setIsUpdating(true);
    try {
      // Update task properties one by one
      const updates = [];

      if (formData.taskName !== selectedTask.name) {
        updates.push(
          apiService.setTaskName(selectedTask.name || "", formData.taskName)
        );
      }

      if (formData.modelId !== selectedTask.model_id) {
        updates.push(
          apiService.setTaskModelId(formData.taskName, formData.modelId)
        );
      }

      if (formData.dataChefId !== selectedTask.interactions_data_chef_id) {
        updates.push(
          apiService.setTaskInteractionsDataChefId(
            formData.taskName,
            formData.dataChefId
          )
        );
      }

      if (
        formData.itemFeaturesDataChefId !==
        (selectedTask.item_features_data_chef_id || "")
      ) {
        updates.push(
          apiService.setTaskItemFeaturesDataChefId(
            formData.taskName,
            formData.itemFeaturesDataChefId
          )
        );
      }

      if (
        formData.userFeaturesDataChefId !==
        (selectedTask.user_features_data_chef_id || "")
      ) {
        updates.push(
          apiService.setTaskUserFeaturesDataChefId(
            formData.taskName,
            formData.userFeaturesDataChefId
          )
        );
      }

      if (formData.interval !== selectedTask.interval) {
        updates.push(
          apiService.setTaskInterval(formData.taskName, formData.interval)
        );
      }

      await Promise.all(updates);

      alert("Task updated successfully!");

      if (user) {
        await activityLogger.log(user.id, user.email, {
          action: "update",
          resourceType: "task",
          resourceId: formData.taskName,
          details: {
            updated_fields: updates.length,
          },
        });
      }

      setShowEditModal(false);
      setSelectedTask(null);
      resetForm();
      fetchTasks();
    } catch (error) {
      alert("Failed to update task");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleRemoveTask = async (task: Task) => {
    const taskName = task.name || task.model_id;
    if (window.confirm(`Are you sure you want to remove task "${taskName}"?`)) {
      try {
        const response = await apiService.removeModelTask(taskName);
        if (response.error) {
          alert("Error: " + response.error);
        } else {
          alert("Task removed successfully!");

          if (user) {
            await activityLogger.log(user.id, user.email, {
              action: "delete",
              resourceType: "task",
              resourceId: taskName,
              details: {},
            });
          }

          fetchTasks();
        }
      } catch (error) {
        alert("Failed to remove task");
      }
    }
  };

  const resetForm = () => {
    setFormData({
      taskName: "",
      modelId: "",
      dataChefId: "",
      itemFeaturesDataChefId: "",
      userFeaturesDataChefId: "",
      interval: 3600,
    });
  };

  const formatInterval = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}d`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "badge-success";
      case "paused":
        return "badge-warning";
      case "completed":
        return "badge-info";
      default:
        return "badge-ghost";
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="loading loading-spinner loading-lg"></div>
          <p className="text-base-content/70 mt-4">Loading tasks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-base-content mb-2">Tasks</h1>
          <p className="text-base-content/70">
            Manage your scheduled model training tasks
          </p>
        </div>
        <button
          onClick={() => {
            fetchModelsAndDataChefs();
            setShowCreateModal(true);
          }}
          className="btn btn-primary gap-2"
        >
          <Plus className="h-5 w-5" />
          <span>Create Task</span>
        </button>
      </div>

      {/* Tasks Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tasks.map((task, index) => (
          <div
            key={index}
            className="card bg-base-100 shadow-sm hover:shadow-md transition-shadow duration-200"
          >
            <div className="card-body">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-primary/10 p-2 rounded-lg">
                  <Calendar className="h-6 w-6 text-primary" />
                </div>
                <div
                  className={`badge ${getStatusColor(
                    task.status || "running"
                  )}`}
                >
                  {task.status || "running"}
                </div>
              </div>

              <h3 className="card-title text-base-content mb-2">
                {task.name || `Task_${task.model_id}`}
              </h3>
              <div className="space-y-2 mb-4">
                <p className="text-sm text-base-content/70">
                  Model: <span className="font-medium">{task.model_id}</span>
                </p>
                <p className="text-sm text-base-content/70">
                  Interactions Data:{" "}
                  <span className="font-medium">
                    {task.interactions_data_chef_id}
                  </span>
                </p>
                {task.item_features_data_chef_id && (
                  <p className="text-sm text-base-content/70">
                    Item Features:{" "}
                    <span className="font-medium">
                      {task.item_features_data_chef_id}
                    </span>
                  </p>
                )}
                {task.user_features_data_chef_id && (
                  <p className="text-sm text-base-content/70">
                    User Features:{" "}
                    <span className="font-medium">
                      {task.user_features_data_chef_id}
                    </span>
                  </p>
                )}
                <div className="flex items-center space-x-1 text-sm text-base-content/70">
                  <Clock className="h-4 w-4" />
                  <span>Every {formatInterval(task.interval)}</span>
                </div>
              </div>

              <div className="card-actions justify-end">
                <button
                  onClick={() => handleEditTask(task)}
                  className="btn btn-info btn-sm gap-1"
                >
                  <Edit className="h-4 w-4" />
                  <span>Edit</span>
                </button>
                <button
                  onClick={() => handleRemoveTask(task)}
                  className="btn btn-error btn-sm"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {tasks.length === 0 && (
        <div className="text-center py-12">
          <Calendar className="h-12 w-12 text-base-content/40 mx-auto mb-4" />
          <p className="text-base-content/70 text-lg">No tasks found</p>
          <p className="text-base-content/50 text-sm">
            Create your first task to get started
          </p>
        </div>
      )}

      {/* Edit Task Modal */}
      {showEditModal && selectedTask && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Edit Task: {selectedTask.name || selectedTask.model_id}
            </h2>
            <form onSubmit={handleUpdateTask} className="space-y-4">
              <div>
                <label className="label">
                  <span className="label-text">Task Name</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.taskName}
                  onChange={(e) =>
                    setFormData({ ...formData, taskName: e.target.value })
                  }
                  className="input input-bordered w-full"
                  placeholder="my_training_task"
                />
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Model ID</span>
                </label>
                {loadingResources ? (
                  <div className="flex items-center justify-center p-3 bg-base-200 rounded-lg">
                    <div className="loading loading-spinner loading-sm mr-2"></div>
                    <span className="text-sm text-base-content/70">Loading models...</span>
                  </div>
                ) : (
                  <select
                    required
                    value={formData.modelId}
                    onChange={(e) =>
                      setFormData({ ...formData, modelId: e.target.value })
                    }
                    className="select select-bordered w-full"
                  >
                    <option value="" disabled>
                      Select a model
                    </option>
                    {models.map((model) => (
                      <option key={model.model_id} value={model.model_id}>
                        {model.model_name} ({model.model_id})
                      </option>
                    ))}
                  </select>
                )}
                {!loadingResources && models.length === 0 && (
                  <p className="text-xs text-warning mt-1">
                    No models found. Please create a model first.
                  </p>
                )}
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Interactions Data Chef ID</span>
                </label>
                {loadingResources ? (
                  <div className="flex items-center justify-center p-3 bg-base-200 rounded-lg">
                    <div className="loading loading-spinner loading-sm mr-2"></div>
                    <span className="text-sm text-base-content/70">Loading data chefs...</span>
                  </div>
                ) : (
                  <select
                    required
                    value={formData.dataChefId}
                    onChange={(e) =>
                      setFormData({ ...formData, dataChefId: e.target.value })
                    }
                    className="select select-bordered w-full"
                  >
                    <option value="" disabled>
                      Select a data chef
                    </option>
                    {dataChefs.map((chef) => (
                      <option key={chef.id} value={chef.id}>
                        {chef.name} ({chef.type})
                      </option>
                    ))}
                  </select>
                )}
                {!loadingResources && dataChefs.length === 0 && (
                  <p className="text-xs text-warning mt-1">
                    No data chefs found. Please create a data chef first.
                  </p>
                )}
              </div>

              <div>
                <label className="label">
                  <span className="label-text">
                    Item Features Data Chef ID (Optional)
                  </span>
                </label>
                {loadingResources ? (
                  <div className="flex items-center justify-center p-3 bg-base-200 rounded-lg">
                    <div className="loading loading-spinner loading-sm mr-2"></div>
                    <span className="text-sm text-base-content/70">Loading data chefs...</span>
                  </div>
                ) : (
                  <select
                    value={formData.itemFeaturesDataChefId}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        itemFeaturesDataChefId: e.target.value,
                      })
                    }
                    className="select select-bordered w-full"
                  >
                    <option value="">None</option>
                    {dataChefs.map((chef) => (
                      <option key={chef.id} value={chef.id}>
                        {chef.name} ({chef.type})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="label">
                  <span className="label-text">
                    User Features Data Chef ID (Optional)
                  </span>
                </label>
                {loadingResources ? (
                  <div className="flex items-center justify-center p-3 bg-base-200 rounded-lg">
                    <div className="loading loading-spinner loading-sm mr-2"></div>
                    <span className="text-sm text-base-content/70">Loading data chefs...</span>
                  </div>
                ) : (
                  <select
                    value={formData.userFeaturesDataChefId}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        userFeaturesDataChefId: e.target.value,
                      })
                    }
                    className="select select-bordered w-full"
                  >
                    <option value="">None</option>
                    {dataChefs.map((chef) => (
                      <option key={chef.id} value={chef.id}>
                        {chef.name} ({chef.type})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="label">
                  <span className="label-text">
                    Interval: {formData.interval} seconds ({formatInterval(formData.interval)})
                  </span>
                </label>
                <input
                  type="range"
                  min="60"
                  max="86400"
                  step="60"
                  value={formData.interval}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      interval: parseInt(e.target.value),
                    })
                  }
                  className="range range-primary"
                />
                <div className="w-full flex justify-between text-xs px-2 text-base-content/60">
                  <span>1 min</span>
                  <span>6 hrs</span>
                  <span>12 hrs</span>
                  <span>24 hrs</span>
                </div>
              </div>

              <div className="modal-action">
                <button
                  type="submit"
                  disabled={isUpdating}
                  className="btn btn-primary"
                >
                  {isUpdating ? "Updating..." : "Update Task"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setSelectedTask(null);
                    resetForm();
                  }}
                  className="btn btn-ghost"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* Create Task Modal */}
      {showCreateModal && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Create New Task
            </h2>
            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="label">
                  <span className="label-text">Task Name</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.taskName}
                  onChange={(e) =>
                    setFormData({ ...formData, taskName: e.target.value })
                  }
                  className="input input-bordered w-full"
                  placeholder="my_training_task"
                />
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Model ID</span>
                </label>
                {loadingResources ? (
                  <div className="flex items-center justify-center p-3 bg-base-200 rounded-lg">
                    <div className="loading loading-spinner loading-sm mr-2"></div>
                    <span className="text-sm text-base-content/70">Loading models...</span>
                  </div>
                ) : (
                  <select
                    required
                    value={formData.modelId}
                    onChange={(e) =>
                      setFormData({ ...formData, modelId: e.target.value })
                    }
                    className="select select-bordered w-full"
                  >
                    <option value="" disabled>
                      Select a model
                    </option>
                    {models.map((model) => (
                      <option key={model.model_id} value={model.model_id}>
                        {model.model_name} ({model.model_id})
                      </option>
                    ))}
                  </select>
                )}
                {!loadingResources && models.length === 0 && (
                  <p className="text-xs text-warning mt-1">
                    No models found. Please create a model first.
                  </p>
                )}
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Interactions Data Chef ID</span>
                </label>
                {loadingResources ? (
                  <div className="flex items-center justify-center p-3 bg-base-200 rounded-lg">
                    <div className="loading loading-spinner loading-sm mr-2"></div>
                    <span className="text-sm text-base-content/70">Loading data chefs...</span>
                  </div>
                ) : (
                  <select
                    required
                    value={formData.dataChefId}
                    onChange={(e) =>
                      setFormData({ ...formData, dataChefId: e.target.value })
                    }
                    className="select select-bordered w-full"
                  >
                    <option value="" disabled>
                      Select a data chef
                    </option>
                    {dataChefs.map((chef) => (
                      <option key={chef.id} value={chef.id}>
                        {chef.name} ({chef.type})
                      </option>
                    ))}
                  </select>
                )}
                {!loadingResources && dataChefs.length === 0 && (
                  <p className="text-xs text-warning mt-1">
                    No data chefs found. Please create a data chef first.
                  </p>
                )}
              </div>

              <div>
                <label className="label">
                  <span className="label-text">
                    Item Features Data Chef ID (Optional)
                  </span>
                </label>
                {loadingResources ? (
                  <div className="flex items-center justify-center p-3 bg-base-200 rounded-lg">
                    <div className="loading loading-spinner loading-sm mr-2"></div>
                    <span className="text-sm text-base-content/70">Loading data chefs...</span>
                  </div>
                ) : (
                  <select
                    value={formData.itemFeaturesDataChefId}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        itemFeaturesDataChefId: e.target.value,
                      })
                    }
                    className="select select-bordered w-full"
                  >
                    <option value="">None</option>
                    {dataChefs.map((chef) => (
                      <option key={chef.id} value={chef.id}>
                        {chef.name} ({chef.type})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="label">
                  <span className="label-text">
                    User Features Data Chef ID (Optional)
                  </span>
                </label>
                {loadingResources ? (
                  <div className="flex items-center justify-center p-3 bg-base-200 rounded-lg">
                    <div className="loading loading-spinner loading-sm mr-2"></div>
                    <span className="text-sm text-base-content/70">Loading data chefs...</span>
                  </div>
                ) : (
                  <select
                    value={formData.userFeaturesDataChefId}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        userFeaturesDataChefId: e.target.value,
                      })
                    }
                    className="select select-bordered w-full"
                  >
                    <option value="">None</option>
                    {dataChefs.map((chef) => (
                      <option key={chef.id} value={chef.id}>
                        {chef.name} ({chef.type})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="label">
                  <span className="label-text">
                    Interval: {formData.interval} seconds ({formatInterval(formData.interval)})
                  </span>
                </label>
                <input
                  type="range"
                  min="60"
                  max="86400"
                  step="60"
                  value={formData.interval}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      interval: parseInt(e.target.value),
                    })
                  }
                  className="range range-primary"
                />
                <div className="w-full flex justify-between text-xs px-2 text-base-content/60">
                  <span>1 min</span>
                  <span>6 hrs</span>
                  <span>12 hrs</span>
                  <span>24 hrs</span>
                </div>
              </div>

              <div className="modal-action">
                <button
                  type="submit"
                  disabled={isCreating}
                  className="btn btn-primary"
                >
                  {isCreating ? "Creating..." : "Create Task"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
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

export default TasksPage;
