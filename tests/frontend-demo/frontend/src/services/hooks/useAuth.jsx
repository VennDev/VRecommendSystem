import { useState, useEffect, useCallback, useContext, createContext } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { authAPI, tokenManager } from '../api'
import toast from 'react-hot-toast'

// Auth Query Keys
export const AUTH_QUERY_KEYS = {
  user: ['auth', 'user'],
  session: ['auth', 'session']
}

// Auth Context
const AuthContext = createContext(null)

// Auth Provider Component
export const AuthProvider = ({ children }) => {
  const [isInitialized, setIsInitialized] = useState(false)
  const queryClient = useQueryClient()

  // Get current user query
  const userQuery = useQuery(
    AUTH_QUERY_KEYS.user,
    authAPI.getCurrentUser,
    {
      retry: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      onSettled: () => {
        setIsInitialized(true)
      }
    }
  )

  // Login mutation
  const loginMutation = useMutation(authAPI.login, {
    onSuccess: (data) => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.user, data.data.user)
      toast.success('Đăng nhập thành công!', {
        icon: '🎉',
        duration: 3000
      })
    },
    onError: (error) => {
      console.error('Login failed:', error)
      const message = error.response?.data?.message || 'Đăng nhập thất bại'
      toast.error(message)
    }
  })

  // Register mutation
  const registerMutation = useMutation(authAPI.register, {
    onSuccess: (data) => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.user, data.data.user)
      toast.success('Đăng ký thành công!', {
        icon: '🎉',
        duration: 3000
      })
    },
    onError: (error) => {
      console.error('Registration failed:', error)
      const message = error.response?.data?.message || 'Đăng ký thất bại'
      toast.error(message)
    }
  })

  // Logout mutation
  const logoutMutation = useMutation(authAPI.logout, {
    onSuccess: () => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.user, null)
      queryClient.clear() // Clear all cached data on logout
      toast.success('Đã đăng xuất', {
        icon: '👋',
        duration: 2000
      })
    },
    onError: (error) => {
      console.error('Logout failed:', error)
      // Still clear user data even if logout request fails
      queryClient.setQueryData(AUTH_QUERY_KEYS.user, null)
      queryClient.clear()
      toast.success('Đã đăng xuất')
    }
  })

  const value = {
    // State
    user: userQuery.data,
    isLoading: userQuery.isLoading,
    isError: userQuery.isError,
    error: userQuery.error,
    isInitialized,
    isAuthenticated: !!userQuery.data && !userQuery.isError,

    // Actions
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    refetchUser: userQuery.refetch,

    // Loading states
    isLoggingIn: loginMutation.isLoading,
    isRegistering: registerMutation.isLoading,
    isLoggingOut: logoutMutation.isLoading
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// Hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}

// Hook for login form
export const useLogin = (options = {}) => {
  const auth = useAuth()
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
    remember: false
  })

  const handleInputChange = useCallback((field, value) => {
    setCredentials(prev => ({
      ...prev,
      [field]: value
    }))
  }, [])

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault()

    // Basic validation
    if (!credentials.username.trim()) {
      toast.error('Vui lòng nhập tên đăng nhập')
      return
    }

    if (!credentials.password.trim()) {
      toast.error('Vui lòng nhập mật khẩu')
      return
    }

    try {
      await auth.login(credentials)

      // Call onSuccess callback if provided
      if (options.onSuccess) {
        options.onSuccess()
      }
    } catch (error) {
      // Error is already handled in the mutation
      if (options.onError) {
        options.onError(error)
      }
    }
  }, [credentials, auth, options])

  const resetForm = useCallback(() => {
    setCredentials({
      username: '',
      password: '',
      remember: false
    })
  }, [])

  return {
    credentials,
    setCredentials,
    handleInputChange,
    handleSubmit,
    resetForm,
    isLoading: auth.isLoggingIn
  }
}

// Hook for registration form
export const useRegister = (options = {}) => {
  const auth = useAuth()
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    fullName: ''
  })

  const [errors, setErrors] = useState({})

  const handleInputChange = useCallback((field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }))
    }
  }, [errors])

  const validateForm = useCallback(() => {
    const newErrors = {}

    // Username validation
    if (!formData.username.trim()) {
      newErrors.username = 'Tên đăng nhập là bắt buộc'
    } else if (formData.username.length < 3) {
      newErrors.username = 'Tên đăng nhập phải có ít nhất 3 ký tự'
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email là bắt buộc'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Định dạng email không hợp lệ'
    }

    // Password validation
    if (!formData.password.trim()) {
      newErrors.password = 'Mật khẩu là bắt buộc'
    } else if (formData.password.length < 6) {
      newErrors.password = 'Mật khẩu phải có ít nhất 6 ký tự'
    }

    // Confirm password validation
    if (!formData.confirmPassword.trim()) {
      newErrors.confirmPassword = 'Xác nhận mật khẩu là bắt buộc'
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Mật khẩu xác nhận không khớp'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [formData])

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault()

    if (!validateForm()) {
      toast.error('Vui lòng kiểm tra lại thông tin')
      return
    }

    try {
      const registrationData = {
        username: formData.username.trim(),
        email: formData.email.trim(),
        password: formData.password,
        full_name: formData.fullName.trim() || formData.username.trim()
      }

      await auth.register(registrationData)

      if (options.onSuccess) {
        options.onSuccess()
      }
    } catch (error) {
      if (options.onError) {
        options.onError(error)
      }
    }
  }, [formData, auth, validateForm, options])

  const resetForm = useCallback(() => {
    setFormData({
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      fullName: ''
    })
    setErrors({})
  }, [])

  return {
    formData,
    setFormData,
    errors,
    handleInputChange,
    handleSubmit,
    resetForm,
    isLoading: auth.isRegistering,
    validateForm
  }
}

// Hook for logout functionality
export const useLogout = (options = {}) => {
  const auth = useAuth()

  const handleLogout = useCallback(async () => {
    try {
      await auth.logout()

      if (options.onSuccess) {
        options.onSuccess()
      }
    } catch (error) {
      if (options.onError) {
        options.onError(error)
      }
    }
  }, [auth, options])

  return {
    logout: handleLogout,
    isLoading: auth.isLoggingOut
  }
}

// Hook for auth guards
export const useAuthGuard = (redirectTo = '/login') => {
  const auth = useAuth()
  const [shouldRedirect, setShouldRedirect] = useState(false)

  useEffect(() => {
    if (auth.isInitialized && !auth.isAuthenticated) {
      setShouldRedirect(true)
    } else {
      setShouldRedirect(false)
    }
  }, [auth.isInitialized, auth.isAuthenticated])

  return {
    isAuthenticated: auth.isAuthenticated,
    isInitialized: auth.isInitialized,
    shouldRedirect,
    redirectTo,
    user: auth.user
  }
}

// Hook for guest guards (redirect if authenticated)
export const useGuestGuard = (redirectTo = '/') => {
  const auth = useAuth()
  const [shouldRedirect, setShouldRedirect] = useState(false)

  useEffect(() => {
    if (auth.isInitialized && auth.isAuthenticated) {
      setShouldRedirect(true)
    } else {
      setShouldRedirect(false)
    }
  }, [auth.isInitialized, auth.isAuthenticated])

  return {
    isAuthenticated: auth.isAuthenticated,
    isInitialized: auth.isInitialized,
    shouldRedirect,
    redirectTo,
    user: auth.user
  }
}

// Hook for token management
export const useTokenManager = () => {
  const queryClient = useQueryClient()

  const refreshToken = useCallback(async () => {
    try {
      const refreshToken = tokenManager.getRefreshToken()
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      const response = await authAPI.refreshToken(refreshToken)
      tokenManager.setToken(response.data.token)

      // Refetch user data
      queryClient.invalidateQueries(AUTH_QUERY_KEYS.user)

      return response.data.token
    } catch (error) {
      console.error('Token refresh failed:', error)
      tokenManager.removeToken()
      queryClient.setQueryData(AUTH_QUERY_KEYS.user, null)
      throw error
    }
  }, [queryClient])

  const clearTokens = useCallback(() => {
    tokenManager.removeToken()
    queryClient.setQueryData(AUTH_QUERY_KEYS.user, null)
    queryClient.clear()
  }, [queryClient])

  return {
    getToken: tokenManager.getToken,
    setToken: tokenManager.setToken,
    removeToken: tokenManager.removeToken,
    refreshToken,
    clearTokens
  }
}

// Hook for session management
export const useSession = () => {
  const auth = useAuth()
  const [sessionInfo, setSessionInfo] = useState({
    startTime: null,
    lastActivity: null,
    isActive: false
  })

  useEffect(() => {
    if (auth.isAuthenticated) {
      const now = Date.now()
      setSessionInfo({
        startTime: now,
        lastActivity: now,
        isActive: true
      })

      // Track user activity
      const updateActivity = () => {
        setSessionInfo(prev => ({
          ...prev,
          lastActivity: Date.now()
        }))
      }

      const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart']
      events.forEach(event => {
        document.addEventListener(event, updateActivity, true)
      })

      return () => {
        events.forEach(event => {
          document.removeEventListener(event, updateActivity, true)
        })
      }
    } else {
      setSessionInfo({
        startTime: null,
        lastActivity: null,
        isActive: false
      })
    }
  }, [auth.isAuthenticated])

  const getSessionDuration = useCallback(() => {
    if (!sessionInfo.startTime) return 0
    return Date.now() - sessionInfo.startTime
  }, [sessionInfo.startTime])

  const getInactivityDuration = useCallback(() => {
    if (!sessionInfo.lastActivity) return 0
    return Date.now() - sessionInfo.lastActivity
  }, [sessionInfo.lastActivity])

  return {
    sessionInfo,
    getSessionDuration,
    getInactivityDuration,
    isActive: sessionInfo.isActive
  }
}

// Hook for role-based access control
export const usePermissions = () => {
  const auth = useAuth()

  const hasPermission = useCallback((permission) => {
    if (!auth.user) return false

    // Add your permission logic here
    // For now, return true for authenticated users
    return auth.isAuthenticated
  }, [auth.user, auth.isAuthenticated])

  const hasRole = useCallback((role) => {
    if (!auth.user) return false

    // Add your role logic here
    // For demo purposes, check if user is admin
    return auth.user.username === 'admin' || auth.user.id === 1
  }, [auth.user])

  const isAdmin = useCallback(() => {
    return hasRole('admin')
  }, [hasRole])

  return {
    hasPermission,
    hasRole,
    isAdmin,
    user: auth.user
  }
}
