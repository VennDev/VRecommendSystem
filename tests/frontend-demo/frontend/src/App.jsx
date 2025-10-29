import React, { Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { motion, AnimatePresence } from "framer-motion";

// Context Providers
import { AuthProvider } from "./services/hooks/useAuth.jsx";

// Layout Components
import Layout from "./components/Layout/Layout";
import LoadingSpinner from "./components/UI/LoadingSpinner";
import ErrorBoundary from "./components/UI/ErrorBoundary";

// Page Components (Lazy loaded)
const Home = React.lazy(() => import("./pages/Home"));
const Products = React.lazy(() => import("./pages/Products"));
const ProductDetail = React.lazy(() => import("./pages/ProductDetail"));
const Login = React.lazy(() => import("./pages/Login"));
const Register = React.lazy(() => import("./pages/Register"));
const Profile = React.lazy(() => import("./pages/Profile"));
const Recommendations = React.lazy(() => import("./pages/Recommendations"));
const LikedProducts = React.lazy(() => import("./pages/LikedProducts"));
const NotFound = React.lazy(() => import("./pages/NotFound"));

// Route Guards
import ProtectedRoute from "./components/Auth/ProtectedRoute";
import GuestRoute from "./components/Auth/GuestRoute";

// Page transition variants
const pageVariants = {
    initial: {
        opacity: 0,
        y: 20,
        scale: 0.98,
    },
    in: {
        opacity: 1,
        y: 0,
        scale: 1,
    },
    out: {
        opacity: 0,
        y: -20,
        scale: 1.02,
    },
};

const pageTransition = {
    type: "tween",
    ease: "anticipate",
    duration: 0.4,
};

// Page wrapper with animations
const AnimatedPage = ({ children }) => (
    <motion.div
        initial="initial"
        animate="in"
        exit="out"
        variants={pageVariants}
        transition={pageTransition}
        className="w-full"
    >
        {children}
    </motion.div>
);

// Loading fallback component
const PageLoadingFallback = () => (
    <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
            <LoadingSpinner size="lg" />
            <p className="mt-4 text-gray-600">Đang tải trang...</p>
        </div>
    </div>
);

// Main App component
function App() {
    return (
        <ErrorBoundary>
            <Helmet>
                <title>
                    VRecommendation Demo - Hệ thống gợi ý sản phẩm thông minh
                </title>
                <meta
                    name="description"
                    content="Demo ứng dụng tích hợp hệ thống gợi ý sản phẩm AI của VRecommendation"
                />
                <meta
                    name="keywords"
                    content="ecommerce, recommendation, AI, machine learning, products"
                />
                <meta property="og:title" content="VRecommendation Demo" />
                <meta
                    property="og:description"
                    content="Hệ thống gợi ý sản phẩm thông minh"
                />
                <meta property="og:type" content="website" />
                <link rel="canonical" href={window.location.origin} />
            </Helmet>

            <AuthProvider>
                <div className="min-h-screen bg-gray-50">
                    <Layout>
                        <AnimatePresence mode="wait">
                            <Suspense fallback={<PageLoadingFallback />}>
                                <Routes>
                                    {/* Public Routes */}
                                    <Route
                                        path="/"
                                        element={
                                            <AnimatedPage>
                                                <Home />
                                            </AnimatedPage>
                                        }
                                    />

                                    <Route
                                        path="/products"
                                        element={
                                            <AnimatedPage>
                                                <Products />
                                            </AnimatedPage>
                                        }
                                    />

                                    <Route
                                        path="/products/:id"
                                        element={
                                            <AnimatedPage>
                                                <ProductDetail />
                                            </AnimatedPage>
                                        }
                                    />

                                    {/* Guest Only Routes */}
                                    <Route
                                        path="/login"
                                        element={
                                            <GuestRoute>
                                                <AnimatedPage>
                                                    <Login />
                                                </AnimatedPage>
                                            </GuestRoute>
                                        }
                                    />

                                    <Route
                                        path="/register"
                                        element={
                                            <GuestRoute>
                                                <AnimatedPage>
                                                    <Register />
                                                </AnimatedPage>
                                            </GuestRoute>
                                        }
                                    />

                                    {/* Protected Routes */}
                                    <Route
                                        path="/profile"
                                        element={
                                            <ProtectedRoute>
                                                <AnimatedPage>
                                                    <Profile />
                                                </AnimatedPage>
                                            </ProtectedRoute>
                                        }
                                    />

                                    <Route
                                        path="/recommendations"
                                        element={
                                            <ProtectedRoute>
                                                <AnimatedPage>
                                                    <Recommendations />
                                                </AnimatedPage>
                                            </ProtectedRoute>
                                        }
                                    />

                                    <Route
                                        path="/liked"
                                        element={
                                            <ProtectedRoute>
                                                <AnimatedPage>
                                                    <LikedProducts />
                                                </AnimatedPage>
                                            </ProtectedRoute>
                                        }
                                    />

                                    {/* Redirect Routes */}
                                    <Route
                                        path="/home"
                                        element={<Navigate to="/" replace />}
                                    />
                                    <Route
                                        path="/dashboard"
                                        element={
                                            <Navigate
                                                to="/recommendations"
                                                replace
                                            />
                                        }
                                    />

                                    {/* 404 Route */}
                                    <Route
                                        path="*"
                                        element={
                                            <AnimatedPage>
                                                <NotFound />
                                            </AnimatedPage>
                                        }
                                    />
                                </Routes>
                            </Suspense>
                        </AnimatePresence>
                    </Layout>
                </div>
            </AuthProvider>
        </ErrorBoundary>
    );
}

export default App;
