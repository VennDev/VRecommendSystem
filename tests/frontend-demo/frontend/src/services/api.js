import axios from 'axios'
import Cookies from 'js-cookie'
import toast from 'react-hot-toast'

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api'
const TOKEN_COOKIE_NAME = 'auth_token'
const REFRESH_TOKEN_COOKIE_NAME = 'refresh_token'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Token management
export const tokenManager = {
  getToken() {
    return Cookies.get(TOKEN_COOKIE_NAME)
  },

  setToken(token, remember = false) {
    const options = remember ? { expires: 30 } : { expires: 1 } // 30 days or 1 day
    Cookies.set(TOKEN_COOKIE_NAME, token, options)
  },

  removeToken() {
    Cookies.remove(TOKEN_COOKIE_NAME)
    Cookies.remove(REFRESH_TOKEN_COOKIE_NAME)
  },

  getRefreshToken() {
    return Cookies.get(REFRESH_TOKEN_COOKIE_NAME)
  },

  setRefreshToken(token, remember = false) {
    const options = remember ? { expires: 30 } : { expires: 1 }
    Cookies.set(REFRESH_TOKEN_COOKIE_NAME, token, options)
  }
}

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = tokenManager.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Log requests in development
    if (import.meta.env.DEV) {
      console.log(`🌐 ${config.method?.toUpperCase()} ${config.url}`, config.data)
    }

    return config
  },
  (error) => {
    console.error('Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => {
    // Log successful responses in development
    if (import.meta.env.DEV) {
      console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data)
    }

    return response
  },
  async (error) => {
    const originalRequest = error.config

    console.error('API Error:', error.response?.data || error.message)

    // Handle token expiration
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = tokenManager.getRefreshToken()
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh-token`, {
            token: refreshToken
          })

          if (response.data.success) {
            const newToken = response.data.data.token
            tokenManager.setToken(newToken)

            // Retry the original request with new token
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return api(originalRequest)
          }
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError)
        tokenManager.removeToken()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }

      // If refresh fails, redirect to login
      tokenManager.removeToken()
      window.location.href = '/login'
    }

    // Handle different error types
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 400:
          toast.error(data.message || 'Dữ liệu không hợp lệ')
          break
        case 401:
          toast.error('Phiên đăng nhập đã hết hạn')
          break
        case 403:
          toast.error('Bạn không có quyền thực hiện hành động này')
          break
        case 404:
          toast.error('Không tìm thấy dữ liệu')
          break
        case 429:
          toast.error('Quá nhiều yêu cầu, vui lòng thử lại sau')
          break
        case 500:
          toast.error('Lỗi máy chủ nội bộ')
          break
        case 503:
          toast.error('Dịch vụ tạm thời không khả dụng')
          break
        default:
          toast.error(data.message || 'Có lỗi xảy ra')
      }
    } else if (error.request) {
      toast.error('Không thể kết nối đến máy chủ')
    } else {
      toast.error('Có lỗi xảy ra khi xử lý yêu cầu')
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  async login(credentials) {
    const response = await api.post('/auth/login', credentials)

    if (response.data.success && response.data.data.token) {
      tokenManager.setToken(response.data.data.token, credentials.remember)
    }

    return response.data
  },

  async register(userData) {
    const response = await api.post('/auth/register', userData)

    if (response.data.success && response.data.data.token) {
      tokenManager.setToken(response.data.data.token)
    }

    return response.data
  },

  async logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.warn('Logout request failed:', error)
    } finally {
      tokenManager.removeToken()
    }
  },

  async verifyToken(token) {
    const response = await api.post('/auth/verify-token', { token })
    return response.data
  },

  async refreshToken(refreshToken) {
    const response = await api.post('/auth/refresh-token', { token: refreshToken })
    return response.data
  },

  async getCurrentUser() {
    const token = tokenManager.getToken()
    if (!token) return null

    try {
      const response = await this.verifyToken(token)
      return response.data.user
    } catch (error) {
      tokenManager.removeToken()
      return null
    }
  }
}

// Products API
export const productsAPI = {
  async getProducts(params = {}) {
    const response = await api.get('/products', { params })
    return response.data
  },

  async getFeaturedProducts(limit = 8) {
    const response = await api.get('/products/featured', {
      params: { limit }
    })
    return response.data
  },

  async getProductById(id) {
    const response = await api.get(`/products/${id}`)
    return response.data
  },

  async getCategories() {
    const response = await api.get('/products/categories')
    return response.data
  },

  async likeProduct(productId) {
    const response = await api.post(`/products/${productId}/like`)
    return response.data
  },

  async getLikedProducts(params = {}) {
    const response = await api.get('/products/user/liked', { params })
    return response.data
  },

  async searchProducts(query, filters = {}) {
    const params = {
      search: query,
      ...filters
    }
    const response = await api.get('/products', { params })
    return response.data
  }
}

// Recommendations API
export const recommendationsAPI = {
  async getRecommendationsForUser(userId, modelId = 'default_model', n = 10) {
    const response = await api.get(`/recommendations/for-user/${userId}`, {
      params: { model_id: modelId, n }
    })
    return response.data
  },

  async getRecommendationsForMe(modelId = 'default_model', n = 10) {
    const response = await api.get('/recommendations/for-me', {
      params: { model_id: modelId, n }
    })
    return response.data
  },

  async getSimilarProducts(productId, limit = 6) {
    const response = await api.get(`/recommendations/similar/${productId}`, {
      params: { limit }
    })
    return response.data
  },

  async submitFeedback(feedback) {
    const response = await api.post('/recommendations/feedback', feedback)
    return response.data
  },

  async getStats() {
    const response = await api.get('/recommendations/stats')
    return response.data
  }
}

// Health check API
export const healthAPI = {
  async check() {
    const response = await api.get('/health')
    return response.data
  },

  async getApiInfo() {
    const response = await api.get('/')
    return response.data
  }
}

// Generic API utilities
export const apiUtils = {
  // Upload file (if needed in the future)
  async uploadFile(file, onProgress = null) {
    const formData = new FormData()
    formData.append('file', file)

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }

    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
        onProgress(percentCompleted)
      }
    }

    const response = await api.post('/upload', formData, config)
    return response.data
  },

  // Cancel request
  cancelToken() {
    return axios.CancelToken.source()
  },

  // Check if error is cancelled request
  isCancel(error) {
    return axios.isCancel(error)
  },

  // Retry failed request
  async retry(originalRequest, maxRetries = 3, delay = 1000) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await api(originalRequest)
      } catch (error) {
        if (i === maxRetries - 1) throw error

        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)))
      }
    }
  }
}

// Connection status monitoring
export const connectionMonitor = {
  isOnline: navigator.onLine,

  init() {
    window.addEventListener('online', () => {
      this.isOnline = true
      toast.success('Kết nối internet đã được khôi phục')
    })

    window.addEventListener('offline', () => {
      this.isOnline = false
      toast.error('Mất kết nối internet')
    })
  },

  checkConnection() {
    return this.isOnline
  }
}

// Initialize connection monitor
connectionMonitor.init()

// Export the configured axios instance as default
export default api

// Export API endpoints for easy access
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    VERIFY: '/auth/verify-token',
    REFRESH: '/auth/refresh-token'
  },
  PRODUCTS: {
    LIST: '/products',
    FEATURED: '/products/featured',
    CATEGORIES: '/products/categories',
    DETAIL: (id) => `/products/${id}`,
    LIKE: (id) => `/products/${id}/like`,
    USER_LIKED: '/products/user/liked'
  },
  RECOMMENDATIONS: {
    FOR_USER: (userId) => `/recommendations/for-user/${userId}`,
    FOR_ME: '/recommendations/for-me',
    SIMILAR: (productId) => `/recommendations/similar/${productId}`,
    FEEDBACK: '/recommendations/feedback',
    STATS: '/recommendations/stats'
  },
  HEALTH: '/health'
}

// Rate limiting helper
export const rateLimiter = {
  requests: new Map(),

  canMakeRequest(endpoint, limit = 60, window = 60000) {
    const now = Date.now()
    const requestKey = endpoint

    if (!this.requests.has(requestKey)) {
      this.requests.set(requestKey, [])
    }

    const requests = this.requests.get(requestKey)

    // Remove old requests outside the window
    const validRequests = requests.filter(time => now - time < window)

    if (validRequests.length >= limit) {
      return false
    }

    validRequests.push(now)
    this.requests.set(requestKey, validRequests)

    return true
  }
}
