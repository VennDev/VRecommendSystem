import {
  Bot,
  Calendar,
  Clock,
  Cpu,
  Database,
  Home,
  LogOut,
  Menu,
  Moon,
  Sun,
  User,
  X,
} from "lucide-react";
import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Layout: React.FC<LayoutProps> = ({
  children,
  activeTab,
  onTabChange,
}) => {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { id: "dashboard", name: "Dashboard", icon: Home },
    { id: "models", name: "Models", icon: Cpu },
    { id: "tasks", name: "Tasks", icon: Calendar },
    { id: "scheduler", name: "Scheduler", icon: Clock },
    { id: "data-chefs", name: "Restaurant Data", icon: Database },
  ];

  return (
    <div className="h-screen bg-base-200 flex">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } fixed inset-y-0 left-0 z-50 w-64 bg-base-100 shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b border-base-300">
          <div className="flex items-center space-x-2">
            <Bot className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold text-base-content">VRecom</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden btn btn-ghost btn-sm"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-5 px-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onTabChange(item.id);
                  setSidebarOpen(false);
                }}
                className={`${
                  activeTab === item.id
                    ? "bg-primary/10 border-r-2 border-primary text-primary"
                    : "text-base-content/70 hover:bg-base-200"
                } group flex items-center px-2 py-2 text-base font-medium rounded-l-md w-full mb-1 transition-all duration-200 btn btn-ghost justify-start`}
              >
                <Icon className="mr-4 h-6 w-6" />
                {item.id === "data-chefs" ? (
                  <>
                    <span>{item.name}</span>
                    <br />
                  </>
                ) : (
                  item.name
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-base-100 shadow-sm border-b border-base-300">
          <div className="flex items-center justify-between h-16 px-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden btn btn-ghost btn-sm"
            >
              <Menu className="h-6 w-6" />
            </button>

            <div className="flex items-center space-x-4">
              <button
                onClick={toggleTheme}
                className="btn btn-ghost btn-circle"
              >
                {isDark ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </button>

              {user && (
                <div className="flex items-center space-x-3">
                  {user.picture ? (
                    <img
                      className="h-8 w-8 rounded-full object-cover"
                      src={user.picture}
                      alt={user.name}
                    />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                      <User className="h-4 w-4 text-primary" />
                    </div>
                  )}
                  <div className="hidden md:block">
                    <div className="text-base font-medium text-base-content">
                      {user.name}
                    </div>
                    <div className="text-sm font-medium text-base-content/70">
                      {user.email}
                    </div>
                  </div>
                  <button onClick={logout} className="btn btn-ghost btn-circle" title="Logout">
                    <LogOut className="h-5 w-5" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Main content area */}
        <main className="flex-1 overflow-auto bg-base-200">{children}</main>
      </div>

      {/* Sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default Layout;
