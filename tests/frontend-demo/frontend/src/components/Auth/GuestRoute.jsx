import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../services/hooks/useAuth.jsx'
import LoadingSpinner from '../UI/LoadingSpinner'

const GuestRoute = ({ children, redirectTo = '/' }) => {
  const { user, isLoading, isInitialized, isAuthenticated } = useAuth()
  const location = useLocation()

  // Show loading while checking authentication
  if (!isInitialized || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" text="Đang kiểm tra trạng thái đăng nhập..." />
      </div>
    )
  }

  // If user is authenticated, redirect to intended destination or home
  if (isAuthenticated) {
    // Get the intended destination from location state or use default
    const from = location.state?.from?.pathname || redirectTo

    return (
      <Navigate
        to={from}
        replace
      />
    )
  }

  // If user is not authenticated, show the guest content
  return children
}

// Higher-order component for guest-only routes
export const withGuestOnly = (Component, options = {}) => {
  return function GuestOnlyComponent(props) {
    return (
      <GuestRoute {...options}>
        <Component {...props} />
      </GuestRoute>
    )
  }
}

export default GuestRoute
