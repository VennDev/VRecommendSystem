import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { ReactQueryDevtools } from 'react-query/devtools'
import { HelmetProvider } from 'react-helmet-async'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import './index.css'

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      refetchOnMount: true,
      refetchOnReconnect: true
    },
    mutations: {
      retry: 1,
      retryDelay: 1000
    }
  }
})

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    })

    // Log error to console in development
    if (import.meta.env.DEV) {
      console.error('Error Boundary caught an error:', error, errorInfo)
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full text-center">
            <div className="text-6xl mb-4">😞</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Oops! Có lỗi xảy ra
            </h1>
            <p className="text-gray-600 mb-6">
              Ứng dụng gặp lỗi không mong muốn. Vui lòng thử tải lại trang.
            </p>
            <div className="space-y-3">
              <button
                onClick={() => window.location.reload()}
                className="w-full bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors"
              >
                Tải lại trang
              </button>
              <button
                onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
                className="w-full bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-300 transition-colors"
              >
                Thử lại
              </button>
            </div>

            {import.meta.env.DEV && this.state.error && (
              <details className="mt-6 text-left">
                <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                  Chi tiết lỗi (Development only)
                </summary>
                <div className="mt-2 p-3 bg-red-50 rounded border text-xs font-mono text-red-800 overflow-auto max-h-40">
                  <div className="font-bold mb-1">Error:</div>
                  <div className="mb-2">{this.state.error.toString()}</div>
                  <div className="font-bold mb-1">Stack trace:</div>
                  <div className="whitespace-pre-wrap">{this.state.errorInfo.componentStack}</div>
                </div>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Toast configuration
const toastOptions = {
  duration: 4000,
  position: 'top-right',
  style: {
    background: '#363636',
    color: '#fff',
    fontSize: '14px',
    borderRadius: '8px',
    padding: '12px 16px'
  },
  success: {
    iconTheme: {
      primary: '#22c55e',
      secondary: '#fff'
    }
  },
  error: {
    iconTheme: {
      primary: '#ef4444',
      secondary: '#fff'
    }
  },
  loading: {
    iconTheme: {
      primary: '#3b82f6',
      secondary: '#fff'
    }
  }
}

// App Wrapper Component
const AppWrapper = () => {
  return (
    <ErrorBoundary>
      <HelmetProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <App />
            <Toaster toastOptions={toastOptions} />
          </BrowserRouter>
          {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
        </QueryClientProvider>
      </HelmetProvider>
    </ErrorBoundary>
  )
}

// Mount the app
const root = ReactDOM.createRoot(document.getElementById('root'))

// Render app
root.render(<AppWrapper />)

// Performance monitoring (development only)
if (import.meta.env.DEV) {
  // Log app startup time
  const startTime = performance.now()

  window.addEventListener('load', () => {
    const loadTime = performance.now() - startTime
    console.log(`🚀 App loaded in ${Math.round(loadTime)}ms`)
  })

  // Log React Query cache
  setTimeout(() => {
    console.log('📊 React Query Cache:', queryClient.getQueryCache())
  }, 1000)
}

// Hot Module Replacement (HMR) support
if (import.meta.hot) {
  import.meta.hot.accept()
}

// Service Worker registration (for future PWA features)
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration)
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError)
      })
  })
}

// Global error handling
window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled promise rejection:', event.reason)

  // Only show user-friendly error in production
  if (import.meta.env.PROD) {
    // Could integrate with error reporting service here
  }
})

// Environment info logging (development only)
if (import.meta.env.DEV) {
  console.log('🔧 Environment:', import.meta.env.MODE)
  console.log('🌐 API Base URL:', import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api')
  console.log('📦 Vite Version:', import.meta.env.VITE_USER_NODE_ENV)
}
