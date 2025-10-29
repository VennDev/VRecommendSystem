import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    }
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      errorId: Date.now().toString(36) + Math.random().toString(36).substr(2)
    }
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    this.setState({
      error: error,
      errorInfo: errorInfo
    })

    // Log to external error reporting service in production
    if (process.env.NODE_ENV === 'production') {
      // Example: logErrorToService(error, errorInfo)
      console.error('Production error:', {
        error: error.toString(),
        errorInfo: errorInfo.componentStack,
        errorId: this.state.errorId,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      })
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    })
  }

  handleReload = () => {
    window.location.reload()
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      const { fallback, showDetails = false } = this.props

      // Custom fallback UI if provided
      if (fallback) {
        return fallback(this.state.error, this.state.errorInfo, this.handleRetry)
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="max-w-2xl w-full text-center"
          >
            {/* Error Icon */}
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
              className="flex justify-center mb-6"
            >
              <div className="p-4 bg-red-100 rounded-full">
                <AlertTriangle className="w-16 h-16 text-red-600" />
              </div>
            </motion.div>

            {/* Error Title */}
            <motion.h1
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="text-3xl font-bold text-gray-900 mb-4"
            >
              Oops! Có lỗi xảy ra
            </motion.h1>

            {/* Error Message */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-gray-600 text-lg mb-2"
            >
              Ứng dụng gặp lỗi không mong muốn. Chúng tôi đã ghi nhận sự cố này.
            </motion.p>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="text-gray-500 mb-8"
            >
              Vui lòng thử lại hoặc liên hệ hỗ trợ nếu vấn đề vẫn tiếp diễn.
            </motion.p>

            {/* Action Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8"
            >
              <button
                onClick={this.handleRetry}
                className="flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              >
                <RefreshCw className="w-4 h-4" />
                Thử lại
              </button>

              <button
                onClick={this.handleReload}
                className="flex items-center gap-2 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-300 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                <RefreshCw className="w-4 h-4" />
                Tải lại trang
              </button>

              <button
                onClick={this.handleGoHome}
                className="flex items-center gap-2 text-primary-600 px-6 py-3 rounded-lg font-medium hover:bg-primary-50 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              >
                <Home className="w-4 h-4" />
                Về trang chủ
              </button>
            </motion.div>

            {/* Error Details (Development Only) */}
            {(process.env.NODE_ENV === 'development' || showDetails) && this.state.error && (
              <motion.details
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
                className="text-left bg-red-50 border border-red-200 rounded-lg p-4"
              >
                <summary className="cursor-pointer text-sm font-medium text-red-700 hover:text-red-800 mb-2">
                  Chi tiết lỗi (Development)
                </summary>
                <div className="mt-2 space-y-2">
                  <div>
                    <div className="text-xs font-medium text-red-700 mb-1">Error ID:</div>
                    <div className="text-xs font-mono text-red-600 bg-red-100 p-2 rounded">
                      {this.state.errorId}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-red-700 mb-1">Error:</div>
                    <div className="text-xs font-mono text-red-600 bg-red-100 p-2 rounded">
                      {this.state.error.toString()}
                    </div>
                  </div>
                  {this.state.errorInfo && (
                    <div>
                      <div className="text-xs font-medium text-red-700 mb-1">Component Stack:</div>
                      <div className="text-xs font-mono text-red-600 bg-red-100 p-2 rounded max-h-40 overflow-auto">
                        <pre className="whitespace-pre-wrap">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </motion.details>
            )}

            {/* Support Info */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="text-xs text-gray-400 mt-6"
            >
              Nếu vấn đề vẫn tiếp diễn, vui lòng liên hệ hỗ trợ với mã lỗi: {this.state.errorId}
            </motion.div>
          </motion.div>
        </div>
      )
    }

    return this.props.children
  }
}

// HOC wrapper for functional components
export const withErrorBoundary = (Component, errorBoundaryProps = {}) => {
  return function WithErrorBoundaryComponent(props) {
    return (
      <ErrorBoundary {...errorBoundaryProps}>
        <Component {...props} />
      </ErrorBoundary>
    )
  }
}

// Hook for error handling in functional components
export const useErrorHandler = () => {
  const [error, setError] = React.useState(null)

  const resetError = React.useCallback(() => {
    setError(null)
  }, [])

  const handleError = React.useCallback((error) => {
    console.error('Error handled by useErrorHandler:', error)
    setError(error)
  }, [])

  React.useEffect(() => {
    if (error) {
      throw error
    }
  }, [error])

  return { handleError, resetError }
}

export default ErrorBoundary
