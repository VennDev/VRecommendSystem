import { useQuery, useMutation, useQueryClient } from 'react-query'
import { recommendationsAPI } from '../api'
import toast from 'react-hot-toast'

// Query keys
export const RECOMMENDATIONS_QUERY_KEYS = {
  all: ['recommendations'],
  forUser: (userId) => [...RECOMMENDATIONS_QUERY_KEYS.all, 'for-user', userId],
  forMe: () => [...RECOMMENDATIONS_QUERY_KEYS.all, 'for-me'],
  similar: (productId) => [...RECOMMENDATIONS_QUERY_KEYS.all, 'similar', productId],
  stats: () => [...RECOMMENDATIONS_QUERY_KEYS.all, 'stats'],
  feedback: () => [...RECOMMENDATIONS_QUERY_KEYS.all, 'feedback']
}

// Get recommendations for specific user
export const useRecommendationsForUser = (userId, modelId = 'default_model', n = 10, options = {}) => {
  return useQuery(
    RECOMMENDATIONS_QUERY_KEYS.forUser(userId),
    () => recommendationsAPI.getRecommendationsForUser(userId, modelId, n),
    {
      enabled: !!userId,
      staleTime: 10 * 60 * 1000, // 10 minutes
      cacheTime: 15 * 60 * 1000, // 15 minutes
      refetchOnWindowFocus: false,
      retry: 2,
      onError: (error) => {
        console.error('Failed to fetch recommendations for user:', error)
        if (!error.response?.status === 503) {
          toast.error('Không thể tải gợi ý sản phẩm')
        }
      },
      onSuccess: (data) => {
        if (data.fallback) {
          toast.info('Đang sử dụng gợi ý dự phòng', {
            duration: 3000,
            icon: '⚠️'
          })
        }
      },
      ...options
    }
  )
}

// Get recommendations for current user
export const useRecommendationsForMe = (modelId = 'default_model', n = 10, options = {}) => {
  return useQuery(
    RECOMMENDATIONS_QUERY_KEYS.forMe(),
    () => recommendationsAPI.getRecommendationsForMe(modelId, n),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: 2,
      onError: (error) => {
        console.error('Failed to fetch my recommendations:', error)
        if (!error.response?.status === 503) {
          toast.error('Không thể tải gợi ý cho bạn')
        }
      },
      onSuccess: (data) => {
        if (data.fallback) {
          toast.info('Đang sử dụng gợi ý dự phòng', {
            duration: 3000,
            icon: '⚠️'
          })
        }
      },
      ...options
    }
  )
}

// Get similar products
export const useSimilarProducts = (productId, limit = 6, options = {}) => {
  return useQuery(
    RECOMMENDATIONS_QUERY_KEYS.similar(productId),
    () => recommendationsAPI.getSimilarProducts(productId, limit),
    {
      enabled: !!productId,
      staleTime: 15 * 60 * 1000, // 15 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
      refetchOnWindowFocus: false,
      retry: 2,
      onError: (error) => {
        console.error('Failed to fetch similar products:', error)
        toast.error('Không thể tải sản phẩm tương tự')
      },
      ...options
    }
  )
}

// Get recommendation stats
export const useRecommendationStats = (options = {}) => {
  return useQuery(
    RECOMMENDATIONS_QUERY_KEYS.stats(),
    recommendationsAPI.getStats,
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: 2,
      onError: (error) => {
        console.error('Failed to fetch recommendation stats:', error)
        toast.error('Không thể tải thống kê gợi ý')
      },
      ...options
    }
  )
}

// Submit recommendation feedback mutation
export const useSubmitFeedback = () => {
  const queryClient = useQueryClient()

  return useMutation(
    recommendationsAPI.submitFeedback,
    {
      onSuccess: (data, variables) => {
        // Show success message based on action
        const { action, product_id } = variables
        let message = 'Cảm ơn phản hồi của bạn!'
        let icon = '👍'

        switch (action) {
          case 'like':
            message = 'Đã ghi nhận bạn thích sản phẩm này'
            icon = '❤️'
            break
          case 'dislike':
            message = 'Đã ghi nhận bạn không thích sản phẩm này'
            icon = '👎'
            break
          case 'view':
            message = 'Đã ghi nhận lượt xem'
            icon = '👁️'
            break
          case 'purchase':
            message = 'Đã ghi nhận giao dịch mua hàng'
            icon = '🛒'
            break
          case 'ignore':
            message = 'Đã ghi nhận bạn bỏ qua sản phẩm này'
            icon = '⏭️'
            break
        }

        toast.success(message, {
          icon: icon,
          duration: 2000
        })

        // Invalidate related queries
        queryClient.invalidateQueries(RECOMMENDATIONS_QUERY_KEYS.stats())
        queryClient.invalidateQueries(RECOMMENDATIONS_QUERY_KEYS.forMe())
      },
      onError: (error) => {
        console.error('Failed to submit feedback:', error)
        toast.error('Không thể gửi phản hồi')
      }
    }
  )
}

// Prefetch recommendations for user
export const usePrefetchRecommendations = () => {
  const queryClient = useQueryClient()

  return {
    prefetchForUser: (userId, modelId = 'default_model', n = 10) => {
      queryClient.prefetchQuery(
        RECOMMENDATIONS_QUERY_KEYS.forUser(userId),
        () => recommendationsAPI.getRecommendationsForUser(userId, modelId, n),
        {
          staleTime: 10 * 60 * 1000,
          cacheTime: 15 * 60 * 1000
        }
      )
    },

    prefetchForMe: (modelId = 'default_model', n = 10) => {
      queryClient.prefetchQuery(
        RECOMMENDATIONS_QUERY_KEYS.forMe(),
        () => recommendationsAPI.getRecommendationsForMe(modelId, n),
        {
          staleTime: 5 * 60 * 1000,
          cacheTime: 10 * 60 * 1000
        }
      )
    },

    prefetchSimilar: (productId, limit = 6) => {
      queryClient.prefetchQuery(
        RECOMMENDATIONS_QUERY_KEYS.similar(productId),
        () => recommendationsAPI.getSimilarProducts(productId, limit),
        {
          staleTime: 15 * 60 * 1000,
          cacheTime: 30 * 60 * 1000
        }
      )
    }
  }
}

// Cache management utilities
export const useRecommendationsCache = () => {
  const queryClient = useQueryClient()

  return {
    // Clear all recommendations cache
    clearAll: () => {
      queryClient.removeQueries(RECOMMENDATIONS_QUERY_KEYS.all)
    },

    // Clear specific user recommendations
    clearForUser: (userId) => {
      queryClient.removeQueries(RECOMMENDATIONS_QUERY_KEYS.forUser(userId))
    },

    // Clear my recommendations
    clearForMe: () => {
      queryClient.removeQueries(RECOMMENDATIONS_QUERY_KEYS.forMe())
    },

    // Clear similar products cache
    clearSimilar: (productId) => {
      queryClient.removeQueries(RECOMMENDATIONS_QUERY_KEYS.similar(productId))
    },

    // Refresh recommendations
    refreshRecommendations: () => {
      queryClient.invalidateQueries(RECOMMENDATIONS_QUERY_KEYS.all)
    },

    // Get cached recommendations
    getCachedRecommendations: (userId) => {
      return queryClient.getQueryData(RECOMMENDATIONS_QUERY_KEYS.forUser(userId))
    },

    getCachedMyRecommendations: () => {
      return queryClient.getQueryData(RECOMMENDATIONS_QUERY_KEYS.forMe())
    },

    // Set cached recommendations
    setCachedRecommendations: (userId, data) => {
      queryClient.setQueryData(RECOMMENDATIONS_QUERY_KEYS.forUser(userId), data)
    },

    setCachedMyRecommendations: (data) => {
      queryClient.setQueryData(RECOMMENDATIONS_QUERY_KEYS.forMe(), data)
    }
  }
}

// Hook to track recommendation interactions
export const useRecommendationTracker = () => {
  const submitFeedback = useSubmitFeedback()

  const trackInteraction = async (productId, action, rating = null) => {
    try {
      await submitFeedback.mutateAsync({
        product_id: productId,
        action: action,
        rating: rating
      })
    } catch (error) {
      console.error('Failed to track interaction:', error)
    }
  }

  const trackView = (productId) => trackInteraction(productId, 'view')
  const trackLike = (productId, rating = 5) => trackInteraction(productId, 'like', rating)
  const trackDislike = (productId, rating = 1) => trackInteraction(productId, 'dislike', rating)
  const trackPurchase = (productId, rating = null) => trackInteraction(productId, 'purchase', rating)
  const trackIgnore = (productId) => trackInteraction(productId, 'ignore')

  return {
    trackView,
    trackLike,
    trackDislike,
    trackPurchase,
    trackIgnore,
    trackInteraction,
    isLoading: submitFeedback.isLoading
  }
}

// Hook for recommendation analytics
export const useRecommendationAnalytics = () => {
  const stats = useRecommendationStats()

  const getInteractionSummary = () => {
    if (!stats.data?.data?.stats) return null

    const { stats: statsData } = stats.data.data

    return {
      totalInteractions: statsData.totalInteractions || 0,
      likedProducts: statsData.likedProducts || 0,
      viewedProducts: statsData.viewedProducts || 0,
      topCategories: statsData.topCategories || [],
      engagementRate: statsData.totalInteractions > 0
        ? ((statsData.likedProducts / statsData.totalInteractions) * 100).toFixed(1)
        : 0
    }
  }

  const getMostInteractedCategory = () => {
    const summary = getInteractionSummary()
    return summary?.topCategories?.[0] || null
  }

  return {
    stats: stats.data,
    isLoading: stats.isLoading,
    error: stats.error,
    getInteractionSummary,
    getMostInteractedCategory,
    refetch: stats.refetch
  }
}

// Hook for recommendation quality assessment
export const useRecommendationQuality = () => {
  const queryClient = useQueryClient()

  const assessRecommendationQuality = (recommendations, userInteractions) => {
    if (!recommendations || !userInteractions) return null

    const totalRecommendations = recommendations.length
    const relevantRecommendations = recommendations.filter(rec => {
      // Check if user has positively interacted with similar items
      return userInteractions.some(interaction =>
        interaction.product_id === rec.id &&
        ['like', 'purchase'].includes(interaction.interaction_type)
      )
    }).length

    const precision = totalRecommendations > 0
      ? (relevantRecommendations / totalRecommendations * 100).toFixed(1)
      : 0

    return {
      totalRecommendations,
      relevantRecommendations,
      precision: parseFloat(precision),
      quality: precision > 70 ? 'high' : precision > 40 ? 'medium' : 'low'
    }
  }

  return {
    assessRecommendationQuality
  }
}
