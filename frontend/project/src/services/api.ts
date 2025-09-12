const API_BASE_URL = "http://localhost:9999/api/v1"; // Update with your actual API base URL

interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

// Updated interfaces based on backend data structures
interface Task {
  model_id: string;
  interactions_data_chef_id: string;
  item_features_data_chef_id?: string | null;
  user_features_data_chef_id?: string | null;
  interval: number;
  name?: string;
}

interface Model {
  model_id: string;
  model_name: string;
  algorithm: string;
  model_type: string;
  status: "training" | "completed" | "failed";
  created_at: string;
  training_completed_at?: string;
  model_metrics?: {
    training_time: number;
    explained_variance_ratio?: number;
    n_users: number;
    n_items: number;
    n_interactions: number;
    sparsity: number;
    n_components?: number;
  };
  final_stats?: {
    total_interactions: number;
    unique_users: number;
    unique_items: number;
    has_user_features: boolean;
    has_item_features: boolean;
  };
}

interface DataChef {
  id: string;
  name: string;
  type: "csv" | "sql" | "api" | "nosql" | "messaging";
  path?: string;
  query?: string;
  url?: string;
  database?: string;
  collection?: string;
  brokers?: string;
  topic?: string;
  group_id?: string;
  rename_columns: string;
  status?: "active" | "inactive" | "error";
  last_updated?: string;
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "API request failed");
      }

      return { data };
    } catch (error) {
      return {
        error:
          error instanceof Error ? error.message : "Unknown error occurred",
      };
    }
  }

  // Model Management
  async createModel(
    modelId: string,
    modelName: string,
    algorithm: string,
    message: string
  ) {
    return this.request(
      `/create_model/${modelId}/${modelName}/${algorithm}/${message}`,
      {
        method: "POST",
      }
    );
  }

  async listModels() {
    return this.request<Model[]>(`/list_models`);
  }

  async getModelInfo(modelId: string) {
    return this.request<Model>(`/get_model_info/${modelId}`);
  }

  async deleteModel(modelId: string) {
    return this.request(`/delete_model/${modelId}`, {
      method: "DELETE",
    });
  }

  // Task Management
  async addModelTask(
    taskName: string,
    modelId: string,
    dataChefId: string,
    interval: number
  ) {
    return this.request(
      `/add_model_task/${taskName}/${modelId}/${dataChefId}/${interval}`,
      {
        method: "POST",
      }
    );
  }

  async removeModelTask(taskName: string) {
    return this.request(`/remove_model_task/${taskName}`, {
      method: "POST",
    });
  }

  async listTasks() {
    return this.request<Task[]>(`/list_tasks`);
  }

  async setTaskName(oldName: string, newName: string) {
    return this.request(`/set_task_name/${oldName}/${newName}`, {
      method: "POST",
    });
  }

  async setTaskModelId(taskName: string, modelId: string) {
    return this.request(`/set_task_model_id/${taskName}/${modelId}`, {
      method: "POST",
    });
  }

  async setTaskInteractionsDataChefId(taskName: string, dataChefId: string) {
    return this.request(
      `/set_task_interactions_data_chef_id/${taskName}/${dataChefId}`,
      {
        method: "POST",
      }
    );
  }

  async setTaskItemFeaturesDataChefId(taskName: string, dataChefId: string) {
    return this.request(
      `/set_task_item_features_data_chef_id/${taskName}/${dataChefId}`,
      {
        method: "POST",
      }
    );
  }

  async setTaskUserFeaturesDataChefId(taskName: string, dataChefId: string) {
    return this.request(
      `/set_task_user_features_data_chef_id/${taskName}/${dataChefId}`,
      {
        method: "POST",
      }
    );
  }

  async setTaskInterval(taskName: string, interval: number) {
    return this.request(`/set_task_interval/${taskName}/${interval}`, {
      method: "POST",
    });
  }

  // Scheduler Management
  async stopScheduler(timeout: number) {
    return this.request(`/stop_scheduler/${timeout}`, {
      method: "POST",
    });
  }

  async restartScheduler(timeout: number) {
    return this.request(`/restart_scheduler/${timeout}`, {
      method: "POST",
    });
  }

  async listSchedulers() {
    return this.request<Task[]>(`/list_schedulers`);
  }

  // Data Chef Management
  async createDataChefFromCsv(
    dataChefId: string,
    filePath: string,
    renameColumns: string
  ) {
    return this.request(
      `/create_data_chef_from_csv/${dataChefId}/${filePath}/${renameColumns}`,
      {
        method: "POST",
      }
    );
  }

  async createDataChefFromSql(
    dataChefId: string,
    query: string,
    renameColumns: string
  ) {
    return this.request(
      `/create_data_chef_from_sql/${dataChefId}/${query}/${renameColumns}`,
      {
        method: "POST",
      }
    );
  }

  async createDataChefFromNoSql(
    dataChefId: string,
    database: string,
    collection: string,
    renameColumns: string
  ) {
    return this.request(
      `/create_data_chef_from_nosql/${dataChefId}/${database}/${collection}/${renameColumns}`,
      {
        method: "POST",
      }
    );
  }

  async createDataChefFromApi(
    dataChefId: string,
    apiEndpoint: string,
    renameColumns: string,
    paginated = false,
    paginationParam = "page",
    sizeParam = "size",
    sizeValue = 100
  ) {
    return this.request(
      `/create_data_chef_from_api/${dataChefId}/${apiEndpoint}/${renameColumns}/${paginated}/${paginationParam}/${sizeParam}/${sizeValue}`,
      {
        method: "POST",
      }
    );
  }

  async createDataChefFromMessageQueue(
    dataChefId: string,
    brokers: string,
    topic: string,
    renameColumns: string,
    groupId: string
  ) {
    return this.request(
      `/create_data_chef_from_message_queue/${dataChefId}/${brokers}/${topic}/${renameColumns}/${groupId}`,
      {
        method: "POST",
      }
    );
  }

  async listDataChefs() {
    return this.request<Record<string, any>>(`/list_data_chefs`);
  }

  async getDataChef(dataChefId: string) {
    return this.request<DataChef>(`/get_data_chef/${dataChefId}`);
  }

  async editDataChef(dataChefId: string, configData: Partial<DataChef>) {
    return this.request(`/edit_data_chef/${dataChefId}`, {
      method: "PUT",
      body: JSON.stringify(configData),
    });
  }

  async deleteDataChef(dataChefId: string) {
    return this.request(`/delete_data_chef/${dataChefId}`, {
      method: "DELETE",
    });
  }
}

export const apiService = new ApiService();
