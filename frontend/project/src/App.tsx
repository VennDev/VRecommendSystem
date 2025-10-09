import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import CallbackPage from "./components/CallbackPage";
import DataChefsPage from "./components/DataChefsPage";
import Layout from "./components/Layout";
import LoginPage from "./components/LoginPage";
import LogsPage from "./components/LogsPage";
import ModelsPage from "./components/ModelsPage";
import SchedulerPage from "./components/SchedulerPage";
import TasksPage from "./components/TasksPage";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ProtectedRoute } from "./components/common/ProtectedRoute";
import { LoadingSpinner } from "./components/common/LoadingSpinner";
import { useRouteHandler } from "./hooks/useRouteHandler";

const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Routes>
      <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/dashboard" replace />} />
      <Route path="/auth/callback" element={<CallbackPage />} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardLayout><Dashboard /></DashboardLayout></ProtectedRoute>} />
      <Route path="/models" element={<ProtectedRoute><DashboardLayout><ModelsPage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/tasks" element={<ProtectedRoute><DashboardLayout><TasksPage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/scheduler" element={<ProtectedRoute><DashboardLayout><SchedulerPage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/data-chefs" element={<ProtectedRoute><DashboardLayout><DataChefsPage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/logs" element={<ProtectedRoute><DashboardLayout><LogsPage /></DashboardLayout></ProtectedRoute>} />
      <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
    </Routes>
  );
};

const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { activeTab, handleTabChange } = useRouteHandler();

  return (
    <Layout activeTab={activeTab} onTabChange={handleTabChange}>
      {children}
    </Layout>
  );
};

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
