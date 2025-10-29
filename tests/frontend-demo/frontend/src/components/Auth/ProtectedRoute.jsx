import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../services/hooks/useAuth.jsx'
import LoadingSpinner from '../UI/LoadingSpinner'

const ProtectedRoute = ({ children, redirectTo = '/login', requireAuth = true }) => {
  const { user, isLoading, isInitialized, isAuthenticated } = useAuth()
  const location = useLocation()

  // Show loading while checking authentication
  if (!isInitialized || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" text="Đang kiểm tra quyền truy cập..." />
      </div>
    )
  }

  // If authentication is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    // Redirect to login with return url
    return (
      <Navigate
        to={redirectTo}
        state={{ from: location }}
        replace
      />
    )
  }

  // If authentication is not required or user is authenticated
  return children
}

// Higher-order component for protecting routes
export const withProtection = (Component, options = {}) => {
  return function ProtectedComponent(props) {
    return (
      <ProtectedRoute {...options}>
        <Component {...props} />
      </ProtectedRoute>
    )
  }
}

// Role-based protection
export const RoleProtectedRoute = ({
  children,
  requiredRole,
  requiredPermission,
  fallback = null,
  redirectTo = '/unauthorized'
}) => {
  const { user, isLoading, isInitialized } = useAuth()

  if (!isInitialized || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" text="Đang kiểm tra quyền truy cập..." />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Check role
  if (requiredRole) {
    const userRole = user.role || (user.id === 1 ? 'admin' : 'user')
    if (userRole !== requiredRole) {
      return fallback || <Navigate to={redirectTo} replace />
    }
  }

  // Check permission
  if (requiredPermission) {
    const userPermissions = user.permissions || []
    if (!userPermissions.includes(requiredPermission)) {
      return fallback || <Navigate to={redirectTo} replace />
    }
  }

  return children
}

export default ProtectedRoute
