const API_BASE_URL = "http://localhost:9999/api/v1";
const AUTH_BASE_URL = "http://localhost:2030"; // Your Go server URL

interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

// Auth related interfaces
interface AuthUser {
  id: string;
  name: string;
  email: string;
  picture: string;
  provider: string;
}

interface AuthResponse {
  success: boolean;
  message: string;
  user?: AuthUser;
}

interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

// Request interfaces for API calls
interface CreateModelRequest {
  model_id: string;
  model_name: string;
  algorithm: string;
  message: string;
}

interface AddModelTaskRequest {
  task_name: string;
  model_id: string;
  data_chef_id: string;
  interval: number;
}

interface RemoveModelTaskRequest {
  task_name: string;
}

interface RenameTaskRequest {
  old_name: string;
  new_name: string;
}

interface UpdateTaskModelIdRequest {
  task_name: string;
  model_id: string;
}

interface UpdateTaskDataChefIdRequest {
  task_name: string;
  data_chef_id: string;
}

interface UpdateTaskIntervalRequest {
  task_name: string;
  interval: number;
}

interface StopSchedulerRequest {
  timeout: number;
}

interface RestartSchedulerRequest {
  timeout: number;
}

interface CreateDataChefFromCsvRequest {
  data_chef_id: string;
  file_path: string;
  rename_columns: string;
}

interface CreateDataChefFromSqlRequest {
  data_chef_id: string;
  query: string;
  rename_columns: string;
}

interface CreateDataChefFromNosqlRequest {
  data_chef_id: string;
  database: string;
  collection: string;
  rename_columns: string;
}

interface CreateDataChefFromApiRequest {
  data_chef_id: string;
  api_endpoint: string;
  rename_columns: string;
  paginated?: boolean;
  pagination_param?: string;
  size_param?: string;
  size_value?: number;
}

interface CreateDataChefFromMessageQueueRequest {
  data_chef_id: string;
  brokers: string;
  topic: string;
  rename_columns: string;
  group_id: string;
}

interface DataChefEditRequest {
  values: Record<string, any>;
}

// Response interfaces based on backend data structures
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
        credentials: "include", // Include cookies for auth
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle auth errors
        if (response.status === 401) {
          window.location.href = "/login";
          return { error: "Authentication required" };
        }
        throw new Error(data.detail || data.error || "API request failed");
      }

      return { data };
    } catch (error) {
      return {
        error:
          error instanceof Error ? error.message : "Unknown error occurred",
      };
    }
  }

  // Auth methods
  async checkAuthStatus(): Promise<ApiResponse<AuthUser>> {
    try {
      const response = await fetch(`${AUTH_BASE_URL}/api/v1/auth/user`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        return { data: data.user };
      }

      return { error: "Not authenticated" };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Auth check failed",
      };
    }
  }

  async logout(): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${AUTH_BASE_URL}/api/v1/auth/logout`, {
        method: "POST",
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        return { data };
      }

      return { error: "Logout failed" };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Logout failed",
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
    const requestBody: CreateModelRequest = {
      model_id: modelId,
      model_name: modelName,
      algorithm,
      message,
    };

    return this.request(`/create_model`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
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
    const requestBody: AddModelTaskRequest = {
      task_name: taskName,
      model_id: modelId,
      data_chef_id: dataChefId,
      interval,
    };

    return this.request(`/add_model_task`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async removeModelTask(taskName: string) {
    const requestBody: RemoveModelTaskRequest = {
      task_name: taskName,
    };

    return this.request(`/remove_model_task`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async listTasks() {
    return this.request<Task[]>(`/list_tasks`);
  }

  async renameTask(oldName: string, newName: string) {
    const requestBody: RenameTaskRequest = {
      old_name: oldName,
      new_name: newName,
    };

    return this.request(`/rename_task`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async updateTaskModelId(taskName: string, modelId: string) {
    const requestBody: UpdateTaskModelIdRequest = {
      task_name: taskName,
      model_id: modelId,
    };

    return this.request(`/update_task_model_id`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async updateTaskInteractionsDataChefId(taskName: string, dataChefId: string) {
    const requestBody: UpdateTaskDataChefIdRequest = {
      task_name: taskName,
      data_chef_id: dataChefId,
    };

    return this.request(`/update_task_interactions_data_chef_id`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async updateTaskItemFeaturesDataChefId(taskName: string, dataChefId: string) {
    const requestBody: UpdateTaskDataChefIdRequest = {
      task_name: taskName,
      data_chef_id: dataChefId,
    };

    return this.request(`/update_task_item_features_data_chef_id`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async updateTaskUserFeaturesDataChefId(taskName: string, dataChefId: string) {
    const requestBody: UpdateTaskDataChefIdRequest = {
      task_name: taskName,
      data_chef_id: dataChefId,
    };

    return this.request(`/update_task_user_features_data_chef_id`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async updateTaskInterval(taskName: string, interval: number) {
    const requestBody: UpdateTaskIntervalRequest = {
      task_name: taskName,
      interval,
    };

    return this.request(`/update_task_interval`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  // Scheduler Management
  async stopScheduler(timeout: number) {
    const requestBody: StopSchedulerRequest = {
      timeout,
    };

    return this.request(`/stop_scheduler`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async restartScheduler(timeout: number) {
    const requestBody: RestartSchedulerRequest = {
      timeout,
    };

    return this.request(`/restart_scheduler`, {
      method: "POST",
      body: JSON.stringify(requestBody),
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
    const requestBody: CreateDataChefFromCsvRequest = {
      data_chef_id: dataChefId,
      file_path: filePath,
      rename_columns: renameColumns,
    };

    return this.request(`/create_data_chef_from_csv`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async createDataChefFromSql(
    dataChefId: string,
    query: string,
    renameColumns: string
  ) {
    const requestBody: CreateDataChefFromSqlRequest = {
      data_chef_id: dataChefId,
      query,
      rename_columns: renameColumns,
    };

    return this.request(`/create_data_chef_from_sql`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async createDataChefFromNoSql(
    dataChefId: string,
    database: string,
    collection: string,
    renameColumns: string
  ) {
    const requestBody: CreateDataChefFromNosqlRequest = {
      data_chef_id: dataChefId,
      database,
      collection,
      rename_columns: renameColumns,
    };

    return this.request(`/create_data_chef_from_nosql`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
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
    const requestBody: CreateDataChefFromApiRequest = {
      data_chef_id: dataChefId,
      api_endpoint: apiEndpoint,
      rename_columns: renameColumns,
      paginated,
      pagination_param: paginationParam,
      size_param: sizeParam,
      size_value: sizeValue,
    };

    return this.request(`/create_data_chef_from_api`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async createDataChefFromMessageQueue(
    dataChefId: string,
    brokers: string,
    topic: string,
    renameColumns: string,
    groupId: string
  ) {
    const requestBody: CreateDataChefFromMessageQueueRequest = {
      data_chef_id: dataChefId,
      brokers,
      topic,
      rename_columns: renameColumns,
      group_id: groupId,
    };

    return this.request(`/create_data_chef_from_message_queue`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async listDataChefs() {
    return this.request<Record<string, any>>(`/list_data_chefs`);
  }

  async getDataChef(dataChefId: string) {
    return this.request<DataChef>(`/get_data_chef/${dataChefId}`);
  }

  async editDataChef(dataChefId: string, configData: Record<string, any>) {
    const requestBody: DataChefEditRequest = {
      values: configData,
    };

    return this.request(`/edit_data_chef/${dataChefId}`, {
      method: "PUT",
      body: JSON.stringify(requestBody),
    });
  }

  async deleteDataChef(dataChefId: string) {
    return this.request(`/delete_data_chef/${dataChefId}`, {
      method: "DELETE",
    });
  }

  async getTotalCountRunTasks() {
    return this.request<ApiResponse<number>>(`/get_total_count_run_tasks`);
  }

  async getTotalRunningTasks() {
    return this.request<ApiResponse<number>>(`/get_total_running_tasks`);
  }

  async getTaskRuntime() {
    return this.request<ApiResponse<number>>(`/get_task_runtime_seconds`);
  }

  async aiServerIsOnline() {
    return this.request<ApiResponse<boolean>>(`/health`);
  }
}

export const apiService = new ApiService();
