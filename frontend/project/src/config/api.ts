// Get environment variables with fallbacks
const getEnvVar = (key: string, defaultValue: string): string => {
  return import.meta.env[key] || defaultValue;
};

// API Configuration - Centralized place for all API settings
export const API_CONFIG = {
  // Base URLs from environment variables
  AI_SERVER_URL: getEnvVar('VITE_AI_SERVER_URL', 'http://localhost:9999'),
  AUTH_SERVER_URL: getEnvVar('VITE_API_SERVER_URL', 'http://localhost:2030'),

  // API Versions
  AI_API_VERSION: "/api/v1",
  AUTH_API_VERSION: "/api/v1",

  // Full base URLs with versions
  get AI_BASE_URL() {
    return `${this.AI_SERVER_URL}${this.AI_API_VERSION}`;
  },

  get AUTH_BASE_URL() {
    return `${this.AUTH_SERVER_URL}${this.AUTH_API_VERSION}`;
  },

  // Timeout settings
  REQUEST_TIMEOUT: 30000, // 30 seconds

  // Request settings
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
  },

  REQUEST_OPTIONS: {
    credentials: 'include' as RequestCredentials,
  },
} as const;

// API Endpoints - All endpoints in one place
export const API_ENDPOINTS = {
  // Authentication endpoints
  AUTH: {
    CHECK_STATUS: '/auth/user',
    LOGIN: (provider: string) => `/auth/${provider}`,
    LOGOUT: '/auth/logout',
    CALLBACK: (provider: string) => `/auth/${provider}/callback`,
  },

  // Activity Logs endpoints
  ACTIVITY_LOGS: {
    CREATE: '/activity-logs',
    GET_USER_LOGS: '/activity-logs/user',
    GET_ALL_RECENT: '/activity-logs/all',
    GET_BY_RESOURCE: '/activity-logs/resource',
    EXPORT: '/activity-logs/export',
  },

  // Server Logs endpoints
  SERVER_LOGS: {
    GET_LOGS: '/server-logs',
  },
  
  // AI Server endpoints
  AI: {
    // Health
    HEALTH: '/health',
    
    // Models
    CREATE_MODEL: '/create_model',
    LIST_MODELS: '/list_models',
    GET_MODEL_INFO: (modelId: string) => `/get_model_info/${modelId}`,
    DELETE_MODEL: (modelId: string) => `/delete_model/${modelId}`,
    
    // Tasks
    ADD_MODEL_TASK: '/add_model_task',
    REMOVE_MODEL_TASK: '/remove_model_task',
    LIST_TASKS: '/list_tasks',
    RENAME_TASK: '/rename_task',
    UPDATE_TASK_MODEL_ID: '/update_task_model_id',
    UPDATE_TASK_INTERACTIONS_DATA_CHEF_ID: '/update_task_interactions_data_chef_id',
    UPDATE_TASK_ITEM_FEATURES_DATA_CHEF_ID: '/update_task_item_features_data_chef_id',
    UPDATE_TASK_USER_FEATURES_DATA_CHEF_ID: '/update_task_user_features_data_chef_id',
    UPDATE_TASK_INTERVAL: '/update_task_interval',
    
    // Scheduler
    STOP_SCHEDULER: '/stop_scheduler',
    RESTART_SCHEDULER: '/restart_scheduler',
    
    // Data Chefs
    CREATE_DATA_CHEF_FROM_CSV: '/create_data_chef_from_csv',
    CREATE_DATA_CHEF_FROM_SQL: '/create_data_chef_from_sql',
    CREATE_DATA_CHEF_FROM_NOSQL: '/create_data_chef_from_nosql',
    CREATE_DATA_CHEF_FROM_API: '/create_data_chef_from_api',
    CREATE_DATA_CHEF_FROM_MESSAGE_QUEUE: '/create_data_chef_from_message_queue',
    LIST_DATA_CHEFS: '/list_data_chefs',
    GET_DATA_CHEF: (dataChefId: string) => `/get_data_chef/${dataChefId}`,
    EDIT_DATA_CHEF: (dataChefId: string) => `/edit_data_chef/${dataChefId}`,
    DELETE_DATA_CHEF: (dataChefId: string) => `/delete_data_chef/${dataChefId}`,
    GET_TOTAL_DATA_CHEFS: '/get_total_data_chefs',
    
    // Metrics
    GET_TOTAL_RUNNING_TASKS: '/get_total_running_tasks',
    GET_TOTAL_COUNT_RUN_TASKS: '/get_total_count_run_tasks',
    GET_TOTAL_ACTIVATED_TASKS: '/get_total_activated_tasks',
    GET_TASK_RUNTIME_SECONDS: '/get_task_runtime_seconds',
    GET_TOTAL_ACTIVATING_MODELS: '/get_total_activating_models',
    GET_TOTAL_TRAINING_MODELS: '/get_total_training_models',
    GET_SCHEDULER_STATUS: '/get_scheduler_status',
    GET_SERVER_LOGS: '/get_server_logs',
    
    // Recommendations
    RECOMMEND: (userId: string, modelId: string, n?: number) => 
      n ? `/recommend/${userId}/${modelId}/${n}` : `/recommend/${userId}/${modelId}`,
  },
} as const;

// Helper function to build full URLs
export const buildUrl = (baseUrl: string, endpoint: string): string => {
  return `${baseUrl}${endpoint}`;
};

// Helper function to build AI server URLs
export const buildAiUrl = (endpoint: string): string => {
  return buildUrl(API_CONFIG.AI_BASE_URL, endpoint);
};

// Helper function to build auth server URLs
export const buildAuthUrl = (endpoint: string): string => {
  return buildUrl(API_CONFIG.AUTH_BASE_URL, endpoint);
};

// Environment-specific overrides (for production, staging, etc.)
export const getApiConfig = () => {
  const env = import.meta.env.MODE;

  // Log current configuration for debugging
  console.log(`[API Config] Environment: ${env}`);
  console.log(`[API Config] AI Server URL: ${API_CONFIG.AI_SERVER_URL}`);
  console.log(`[API Config] Auth Server URL: ${API_CONFIG.AUTH_SERVER_URL}`);

  switch (env) {
    case 'production':
      return {
        ...API_CONFIG,
        AI_SERVER_URL: getEnvVar('VITE_AI_SERVER_URL', API_CONFIG.AI_SERVER_URL),
        AUTH_SERVER_URL: getEnvVar('VITE_API_SERVER_URL', API_CONFIG.AUTH_SERVER_URL),
      };
    case 'staging':
      return {
        ...API_CONFIG,
        AI_SERVER_URL: getEnvVar('VITE_AI_SERVER_URL', 'http://staging-ai.example.com'),
        AUTH_SERVER_URL: getEnvVar('VITE_API_SERVER_URL', 'http://staging-auth.example.com'),
      };
    default:
      return API_CONFIG;
  }
};