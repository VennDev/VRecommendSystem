import {
  API_ENDPOINTS,
  buildAiUrl,
  buildAuthUrl,
  getApiConfig,
} from "../config/api";

const config = getApiConfig();

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
    options: RequestInit = {},
    useAuthServer = false
  ): Promise<ApiResponse<T>> {
    try {
      const baseUrl = useAuthServer ? config.AUTH_BASE_URL : config.AI_BASE_URL;
      const url = `${baseUrl}${endpoint}`;

      // Get JWT token from localStorage
      const token = localStorage.getItem("auth_token");
      const headers: HeadersInit = {
        ...config.DEFAULT_HEADERS,
        ...options.headers,
      };

      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        console.debug(`Request to ${url} with token`);
      } else {
        console.warn(`Request to ${url} WITHOUT token`);
      }

      const response = await fetch(url, {
        ...config.REQUEST_OPTIONS,
        ...options,
        headers,
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
      const response = await fetch(
        buildAuthUrl(API_ENDPOINTS.AUTH.CHECK_STATUS),
        {
          ...config.REQUEST_OPTIONS,
        }
      );

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
      const response = await fetch(buildAuthUrl(API_ENDPOINTS.AUTH.LOGOUT), {
        method: "POST",
        ...config.REQUEST_OPTIONS,
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

    return this.request(API_ENDPOINTS.AI.CREATE_MODEL, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async listModels() {
    return this.request<Model[]>(API_ENDPOINTS.AI.LIST_MODELS);
  }

  async getModelInfo(modelId: string) {
    return this.request<Model>(API_ENDPOINTS.AI.GET_MODEL_INFO(modelId));
  }

  async deleteModel(modelId: string) {
    return this.request(API_ENDPOINTS.AI.DELETE_MODEL(modelId), {
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

    return this.request(API_ENDPOINTS.AI.ADD_MODEL_TASK, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async removeModelTask(taskName: string) {
    const requestBody: RemoveModelTaskRequest = {
      task_name: taskName,
    };

    return this.request(API_ENDPOINTS.AI.REMOVE_MODEL_TASK, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async listTasks() {
    return this.request<Task[]>(API_ENDPOINTS.AI.LIST_TASKS);
  }

  async setTaskName(oldName: string, newName: string) {
    const requestBody: RenameTaskRequest = {
      old_name: oldName,
      new_name: newName,
    };

    return this.request(API_ENDPOINTS.AI.RENAME_TASK, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async setTaskModelId(taskName: string, modelId: string) {
    const requestBody: UpdateTaskModelIdRequest = {
      task_name: taskName,
      model_id: modelId,
    };

    return this.request(API_ENDPOINTS.AI.UPDATE_TASK_MODEL_ID, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async setTaskInteractionsDataChefId(taskName: string, dataChefId: string) {
    const requestBody: UpdateTaskDataChefIdRequest = {
      task_name: taskName,
      data_chef_id: dataChefId,
    };

    return this.request(
      API_ENDPOINTS.AI.UPDATE_TASK_INTERACTIONS_DATA_CHEF_ID,
      {
        method: "POST",
        body: JSON.stringify(requestBody),
      }
    );
  }

  async setTaskItemFeaturesDataChefId(taskName: string, dataChefId: string) {
    const requestBody: UpdateTaskDataChefIdRequest = {
      task_name: taskName,
      data_chef_id: dataChefId,
    };

    return this.request(
      API_ENDPOINTS.AI.UPDATE_TASK_ITEM_FEATURES_DATA_CHEF_ID,
      {
        method: "POST",
        body: JSON.stringify(requestBody),
      }
    );
  }

  async setTaskUserFeaturesDataChefId(taskName: string, dataChefId: string) {
    const requestBody: UpdateTaskDataChefIdRequest = {
      task_name: taskName,
      data_chef_id: dataChefId,
    };

    return this.request(
      API_ENDPOINTS.AI.UPDATE_TASK_USER_FEATURES_DATA_CHEF_ID,
      {
        method: "POST",
        body: JSON.stringify(requestBody),
      }
    );
  }

  async setTaskInterval(taskName: string, interval: number) {
    const requestBody: UpdateTaskIntervalRequest = {
      task_name: taskName,
      interval,
    };

    return this.request(API_ENDPOINTS.AI.UPDATE_TASK_INTERVAL, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  // Scheduler Management
  async stopScheduler(timeout: number) {
    const requestBody: StopSchedulerRequest = {
      timeout,
    };

    return this.request(API_ENDPOINTS.AI.STOP_SCHEDULER, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async restartScheduler(timeout: number) {
    const requestBody: RestartSchedulerRequest = {
      timeout,
    };

    return this.request(API_ENDPOINTS.AI.RESTART_SCHEDULER, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
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

    return this.request(API_ENDPOINTS.AI.CREATE_DATA_CHEF_FROM_CSV, {
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

    return this.request(API_ENDPOINTS.AI.CREATE_DATA_CHEF_FROM_SQL, {
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

    return this.request(API_ENDPOINTS.AI.CREATE_DATA_CHEF_FROM_NOSQL, {
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

    return this.request(API_ENDPOINTS.AI.CREATE_DATA_CHEF_FROM_API, {
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

    return this.request(API_ENDPOINTS.AI.CREATE_DATA_CHEF_FROM_MESSAGE_QUEUE, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  }

  async listDataChefs() {
    return this.request<Record<string, any>>(API_ENDPOINTS.AI.LIST_DATA_CHEFS);
  }

  async getDataChef(dataChefId: string) {
    return this.request<DataChef>(API_ENDPOINTS.AI.GET_DATA_CHEF(dataChefId));
  }

  async editDataChef(dataChefId: string, configData: Record<string, any>) {
    const requestBody: DataChefEditRequest = {
      values: configData,
    };

    return this.request(API_ENDPOINTS.AI.EDIT_DATA_CHEF(dataChefId), {
      method: "PUT",
      body: JSON.stringify(requestBody),
    });
  }

  async deleteDataChef(dataChefId: string) {
    return this.request(API_ENDPOINTS.AI.DELETE_DATA_CHEF(dataChefId), {
      method: "DELETE",
    });
  }

  async getTotalCountRunTasks() {
    return this.request<ApiResponse<number>>(
      API_ENDPOINTS.AI.GET_TOTAL_COUNT_RUN_TASKS
    );
  }

  async getTotalRunningTasks() {
    return this.request<ApiResponse<number>>(
      API_ENDPOINTS.AI.GET_TOTAL_RUNNING_TASKS
    );
  }

  async getTaskRuntime() {
    return this.request<ApiResponse<number>>(
      API_ENDPOINTS.AI.GET_TASK_RUNTIME_SECONDS
    );
  }

  async aiServerIsOnline() {
    return this.request<ApiResponse<boolean>>(API_ENDPOINTS.AI.HEALTH);
  }

  async getSchedulerStatus() {
    return this.request<ApiResponse<{is_running: boolean; status: string}>>(
      API_ENDPOINTS.AI.GET_SCHEDULER_STATUS
    );
  }

  async getServerLogs(limit: number = 50) {
    return this.request<ApiResponse<Array<{timestamp: string; message: string; level: string}>>>(
      `${API_ENDPOINTS.AI.GET_SERVER_LOGS}?limit=${limit}`
    );
  }

  // Recommendation methods
  async getRecommendations(userId: string, modelId: string, n?: number) {
    return this.request(API_ENDPOINTS.AI.RECOMMEND(userId, modelId, n));
  }
}

export const apiService = new ApiService();
