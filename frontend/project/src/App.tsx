import React, { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import CallbackPage from "./components/CallbackPage";
import DataChefsPage from "./components/DataChefsPage";
import Layout from "./components/Layout";
import LoginPage from "./components/LoginPage";
import ModelsPage from "./components/ModelsPage";
import SchedulerPage from "./components/SchedulerPage";
import TasksPage from "./components/TasksPage";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";

const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/dashboard" replace />} />
      <Route path="/auth/callback" element={<CallbackPage />} />
      <Route path="/dashboard" element={user ? <DashboardLayout><Dashboard /></DashboardLayout> : <Navigate to="/login" replace />} />
      <Route path="/models" element={user ? <DashboardLayout><ModelsPage /></DashboardLayout> : <Navigate to="/login" replace />} />
      <Route path="/tasks" element={user ? <DashboardLayout><TasksPage /></DashboardLayout> : <Navigate to="/login" replace />} />
      <Route path="/scheduler" element={user ? <DashboardLayout><SchedulerPage /></DashboardLayout> : <Navigate to="/login" replace />} />
      <Route path="/data-chefs" element={user ? <DashboardLayout><DataChefsPage /></DashboardLayout> : <Navigate to="/login" replace />} />
      <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
    </Routes>
  );
};

const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = useState(() => {
    const path = window.location.pathname;
    if (path.includes('/models')) return 'models';
    if (path.includes('/tasks')) return 'tasks';
    if (path.includes('/scheduler')) return 'scheduler';
    if (path.includes('/data-chefs')) return 'data-chefs';
    return 'dashboard';
  });

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    // Navigate to the corresponding route
    window.history.pushState(null, '', `/${tab === 'dashboard' ? 'dashboard' : tab}`);
  };

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
