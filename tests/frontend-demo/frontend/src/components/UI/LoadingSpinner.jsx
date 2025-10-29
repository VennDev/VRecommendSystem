import React from 'react'
import { motion } from 'framer-motion'

const LoadingSpinner = ({
  size = 'md',
  color = 'primary',
  text = null,
  className = '',
  inline = false
}) => {
  // Size variants
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  }

  // Color variants
  const colors = {
    primary: 'border-primary-600',
    secondary: 'border-gray-600',
    white: 'border-white',
    success: 'border-green-600',
    warning: 'border-yellow-600',
    error: 'border-red-600'
  }

  // Animation variants
  const spinVariants = {
    start: {
      rotate: 0,
    },
    end: {
      rotate: 360,
    },
  }

  const spinTransition = {
    duration: 1,
    repeat: Infinity,
    ease: 'linear',
  }

  const containerClass = inline
    ? 'inline-flex items-center gap-3'
    : 'flex flex-col items-center justify-center gap-3'

  return (
    <div className={`${containerClass} ${className}`}>
      <motion.div
        className={`
          ${sizes[size]}
          border-2
          ${colors[color]}
          border-t-transparent
          rounded-full
        `}
        variants={spinVariants}
        initial="start"
        animate="end"
        transition={spinTransition}
        role="status"
        aria-label="Loading"
      />
      {text && (
        <motion.p
          className="text-sm text-gray-600 font-medium"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          {text}
        </motion.p>
      )}
    </div>
  )
}

// Preset spinner variants
LoadingSpinner.Inline = ({ children, isLoading, ...props }) => {
  if (!isLoading) return children

  return (
    <LoadingSpinner
      inline
      size="sm"
      text="Đang tải..."
      {...props}
    />
  )
}

LoadingSpinner.Page = (props) => (
  <div className="flex items-center justify-center min-h-[50vh]">
    <LoadingSpinner
      size="lg"
      text="Đang tải trang..."
      {...props}
    />
  </div>
)

LoadingSpinner.Button = (props) => (
  <LoadingSpinner
    size="sm"
    color="white"
    inline
    {...props}
  />
)

export default LoadingSpinner
