import {
    useQuery,
    useMutation,
    useQueryClient,
    useInfiniteQuery,
} from "react-query";
import { useState, useCallback } from "react";
import { productsAPI } from "../api";
import toast from "react-hot-toast";

// Query keys
export const PRODUCTS_QUERY_KEYS = {
    all: ["products"],
    lists: () => [...PRODUCTS_QUERY_KEYS.all, "list"],
    list: (filters) => [...PRODUCTS_QUERY_KEYS.lists(), filters],
    details: () => [...PRODUCTS_QUERY_KEYS.all, "detail"],
    detail: (id) => [...PRODUCTS_QUERY_KEYS.details(), id],
    featured: () => [...PRODUCTS_QUERY_KEYS.all, "featured"],
    categories: () => [...PRODUCTS_QUERY_KEYS.all, "categories"],
    liked: () => [...PRODUCTS_QUERY_KEYS.all, "liked"],
    search: (query) => [...PRODUCTS_QUERY_KEYS.all, "search", query],
};

// Get products with pagination and filters
export const useProducts = (params = {}) => {
    return useQuery(
        PRODUCTS_QUERY_KEYS.list(params),
        () => productsAPI.getProducts(params),
        {
            keepPreviousData: true,
            staleTime: 5 * 60 * 1000, // 5 minutes
            cacheTime: 10 * 60 * 1000, // 10 minutes
            refetchOnWindowFocus: false,
            retry: 2,
            onError: (error) => {
                console.error("Failed to fetch products:", error);
                toast.error("Không thể tải danh sách sản phẩm");
            },
        },
    );
};

// Get featured products
export const useFeaturedProducts = (limit = 8) => {
    return useQuery(
        PRODUCTS_QUERY_KEYS.featured(),
        () => productsAPI.getFeaturedProducts(limit),
        {
            staleTime: 10 * 60 * 1000, // 10 minutes
            cacheTime: 15 * 60 * 1000, // 15 minutes
            refetchOnWindowFocus: false,
            retry: 2,
            onError: (error) => {
                console.error("Failed to fetch featured products:", error);
                toast.error("Không thể tải sản phẩm nổi bật");
            },
        },
    );
};

// Get single product by ID
export const useProduct = (productId, options = {}) => {
    return useQuery(
        PRODUCTS_QUERY_KEYS.detail(productId),
        () => productsAPI.getProductById(productId),
        {
            enabled: !!productId,
            staleTime: 5 * 60 * 1000, // 5 minutes
            cacheTime: 10 * 60 * 1000, // 10 minutes
            retry: 2,
            onError: (error) => {
                console.error("Failed to fetch product:", error);
                toast.error("Không thể tải thông tin sản phẩm");
            },
            ...options,
        },
    );
};

// Get categories
export const useCategories = () => {
    return useQuery(
        PRODUCTS_QUERY_KEYS.categories(),
        productsAPI.getCategories,
        {
            staleTime: 30 * 60 * 1000, // 30 minutes
            cacheTime: 60 * 60 * 1000, // 1 hour
            refetchOnWindowFocus: false,
            retry: 2,
            onError: (error) => {
                console.error("Failed to fetch categories:", error);
                toast.error("Không thể tải danh mục sản phẩm");
            },
        },
    );
};

// Get liked products
export const useLikedProducts = (params = {}) => {
    return useQuery(
        PRODUCTS_QUERY_KEYS.liked(),
        () => productsAPI.getLikedProducts(params),
        {
            keepPreviousData: true,
            staleTime: 2 * 60 * 1000, // 2 minutes
            cacheTime: 5 * 60 * 1000, // 5 minutes
            refetchOnWindowFocus: false,
            retry: 2,
            onError: (error) => {
                console.error("Failed to fetch liked products:", error);
                toast.error("Không thể tải sản phẩm đã thích");
            },
        },
    );
};

// Search products
export const useSearchProducts = (query, filters = {}, options = {}) => {
    return useQuery(
        PRODUCTS_QUERY_KEYS.search(query),
        () => productsAPI.searchProducts(query, filters),
        {
            enabled: !!query && query.length >= 2,
            keepPreviousData: true,
            staleTime: 2 * 60 * 1000, // 2 minutes
            cacheTime: 5 * 60 * 1000, // 5 minutes
            retry: 2,
            onError: (error) => {
                console.error("Failed to search products:", error);
                toast.error("Không thể tìm kiếm sản phẩm");
            },
            ...options,
        },
    );
};

// Like/Unlike product mutation
export const useLikeProduct = () => {
    const queryClient = useQueryClient();

    return useMutation(productsAPI.likeProduct, {
        onMutate: async (productId) => {
            // Cancel any outgoing refetches
            await queryClient.cancelQueries(
                PRODUCTS_QUERY_KEYS.detail(productId),
            );
            await queryClient.cancelQueries(PRODUCTS_QUERY_KEYS.lists());
            await queryClient.cancelQueries(PRODUCTS_QUERY_KEYS.liked());

            // Snapshot the previous value
            const previousProduct = queryClient.getQueryData(
                PRODUCTS_QUERY_KEYS.detail(productId),
            );
            const previousProducts = queryClient.getQueryData(
                PRODUCTS_QUERY_KEYS.lists(),
            );
            const previousLikedProducts = queryClient.getQueryData(
                PRODUCTS_QUERY_KEYS.liked(),
            );

            // Optimistically update product detail
            if (previousProduct?.data?.product) {
                queryClient.setQueryData(
                    PRODUCTS_QUERY_KEYS.detail(productId),
                    (old) => ({
                        ...old,
                        data: {
                            ...old.data,
                            product: {
                                ...old.data.product,
                                is_liked: old.data.product.is_liked ? 0 : 1,
                            },
                        },
                    }),
                );
            }

            // Optimistically update products list
            queryClient.setQueriesData(
                { queryKey: PRODUCTS_QUERY_KEYS.lists() },
                (old) => {
                    if (!old?.data?.products) return old;

                    return {
                        ...old,
                        data: {
                            ...old.data,
                            products: old.data.products.map((product) =>
                                product.id === parseInt(productId)
                                    ? {
                                          ...product,
                                          is_liked: product.is_liked ? 0 : 1,
                                      }
                                    : product,
                            ),
                        },
                    };
                },
            );

            return { previousProduct, previousProducts, previousLikedProducts };
        },

        onError: (error, productId, context) => {
            console.error("Failed to like/unlike product:", error);

            // Rollback optimistic updates
            if (context?.previousProduct) {
                queryClient.setQueryData(
                    PRODUCTS_QUERY_KEYS.detail(productId),
                    context.previousProduct,
                );
            }
            if (context?.previousProducts) {
                queryClient.setQueryData(
                    PRODUCTS_QUERY_KEYS.lists(),
                    context.previousProducts,
                );
            }
            if (context?.previousLikedProducts) {
                queryClient.setQueryData(
                    PRODUCTS_QUERY_KEYS.liked(),
                    context.previousLikedProducts,
                );
            }

            toast.error("Không thể cập nhật trạng thái yêu thích");
        },

        onSuccess: (data, productId) => {
            const action = data.data?.action;
            const message =
                action === "liked"
                    ? "Đã thêm vào yêu thích"
                    : "Đã bỏ yêu thích";

            toast.success(message, {
                icon: action === "liked" ? "❤️" : "💔",
                duration: 2000,
            });

            // Invalidate related queries to ensure consistency
            queryClient.invalidateQueries(PRODUCTS_QUERY_KEYS.liked());
        },

        onSettled: (data, error, productId) => {
            // Always refetch to ensure server state is correct
            queryClient.invalidateQueries(
                PRODUCTS_QUERY_KEYS.detail(productId),
            );
        },
    });
};

// Custom hook for infinite products loading
export const useInfiniteProducts = (initialParams = {}) => {
    return useInfiniteQuery(
        [...PRODUCTS_QUERY_KEYS.lists(), "infinite", initialParams],
        ({ pageParam = 1 }) =>
            productsAPI.getProducts({ ...initialParams, page: pageParam }),
        {
            getNextPageParam: (lastPage) => {
                const { pagination } = lastPage.data;
                return pagination.has_next
                    ? pagination.current_page + 1
                    : undefined;
            },
            getPreviousPageParam: (firstPage) => {
                const { pagination } = firstPage.data;
                return pagination.has_prev
                    ? pagination.current_page - 1
                    : undefined;
            },
            keepPreviousData: true,
            staleTime: 5 * 60 * 1000,
            cacheTime: 10 * 60 * 1000,
            refetchOnWindowFocus: false,
            retry: 2,
            onError: (error) => {
                console.error("Failed to fetch infinite products:", error);
                toast.error("Không thể tải thêm sản phẩm");
            },
        },
    );
};

// Prefetch product details
export const usePrefetchProduct = () => {
    const queryClient = useQueryClient();

    return (productId) => {
        queryClient.prefetchQuery(
            PRODUCTS_QUERY_KEYS.detail(productId),
            () => productsAPI.getProductById(productId),
            {
                staleTime: 5 * 60 * 1000,
                cacheTime: 10 * 60 * 1000,
            },
        );
    };
};

// Cache management utilities
export const useProductsCache = () => {
    const queryClient = useQueryClient();

    return {
        // Clear all products cache
        clearAll: () => {
            queryClient.removeQueries(PRODUCTS_QUERY_KEYS.all);
        },

        // Clear specific product cache
        clearProduct: (productId) => {
            queryClient.removeQueries(PRODUCTS_QUERY_KEYS.detail(productId));
        },

        // Refresh products list
        refreshProducts: () => {
            queryClient.invalidateQueries(PRODUCTS_QUERY_KEYS.lists());
        },

        // Get cached product
        getCachedProduct: (productId) => {
            return queryClient.getQueryData(
                PRODUCTS_QUERY_KEYS.detail(productId),
            );
        },

        // Set cached product
        setCachedProduct: (productId, data) => {
            queryClient.setQueryData(
                PRODUCTS_QUERY_KEYS.detail(productId),
                data,
            );
        },
    };
};

// Custom hook for product filters state management
export const useProductFilters = (initialFilters = {}) => {
    const [filters, setFilters] = useState(initialFilters);

    const updateFilter = useCallback((key, value) => {
        setFilters((prev) => ({
            ...prev,
            [key]: value,
            page: 1, // Reset page when filter changes
        }));
    }, []);

    const resetFilters = useCallback(() => {
        setFilters(initialFilters);
    }, [initialFilters]);

    const removeFilter = useCallback((key) => {
        setFilters((prev) => {
            const newFilters = { ...prev };
            delete newFilters[key];
            return { ...newFilters, page: 1 };
        });
    }, []);

    return {
        filters,
        setFilters,
        updateFilter,
        resetFilters,
        removeFilter,
    };
};
