import React, { useState } from "react";
import Dashboard from "./components/Dashboard";
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
  const [activeTab, setActiveTab] = useState("dashboard");

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

  if (!user) {
    return <LoginPage />;
  }

  const renderContent = () => {
    switch (activeTab) {
      case "dashboard":
        return <Dashboard />;
      case "models":
        return <ModelsPage />;
      case "tasks":
        return <TasksPage />;
      case "scheduler":
        return <SchedulerPage />;
      case "data-chefs":
        return <DataChefsPage />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {renderContent()}
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
