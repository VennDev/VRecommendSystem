import { Activity, CircleAlert as AlertCircle, Calendar, CircleCheck as CheckCircle, Clock, Cpu, Database, TrendingUp, User, Server } from "lucide-react";
import React, { useEffect, useState } from "react";
import { apiService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { healthCheckService, ServerHealth } from "../services/healthCheck";

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalTasks: 0,
    runningTasks: 0,
    dataChefs: 0,
    activeModels: 0,
    isServerOnline: false,
  });

  const [serverHealth, setServerHealth] = useState<ServerHealth[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<{is_running: boolean; status: string} | null>(null);

  const [recentActivity] = useState([
    {
      id: 1,
      action: "Model trained successfully",
      time: "2 minutes ago",
      type: "success",
    },
    {
      id: 2,
      action: "New task scheduled",
      time: "5 minutes ago",
      type: "info",
    },
    {
      id: 3,
      action: "Data chef created from API",
      time: "10 minutes ago",
      type: "success",
    },
    {
      id: 4,
      action: "Scheduler restarted",
      time: "15 minutes ago",
      type: "warning",
    },
  ]);

  useEffect(() => {
    fetchDashboardData();
    checkServerHealth();
    checkSchedulerStatus();

    // Check server health every 30 seconds
    const healthCheckInterval = setInterval(() => {
      checkServerHealth();
      checkSchedulerStatus();
    }, 30000);

    return () => clearInterval(healthCheckInterval);
  }, []);

  const checkServerHealth = async () => {
    const health = await healthCheckService.checkAllServers();
    setServerHealth(health);
  };

  const checkSchedulerStatus = async () => {
    try {
      const response = await apiService.getSchedulerStatus();
      if (response.data) {
        setSchedulerStatus(response.data);
      }
    } catch (error) {
      console.error('Failed to check scheduler status:', error);
    }
  };

  const fetchDashboardData = async () => {
    try {
      const [
        tasksResponse,
        dataChefResponse,
        runningTasksResponse,
        listModelsResponse,
        serverStatusResponse,
      ] = await Promise.all([
        apiService.listTasks(),
        apiService.listDataChefs(),
        apiService.getTotalRunningTasks(),
        apiService.listModels(),
        apiService.aiServerIsOnline(),
      ]);

      setStats({
        totalTasks: Object.keys(tasksResponse).length || 0,
        runningTasks: runningTasksResponse.data?.data || 0,
        dataChefs: Object.keys(dataChefResponse.data || {}).length || 0,
        activeModels: Object.keys(listModelsResponse.data || {}).length || 0, // Mock data
        isServerOnline: serverStatusResponse.data?.status == "ok" || false,
      });
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    }
  };

  const statCards = [
    {
      title: "Active Models",
      value: stats.activeModels,
      icon: Cpu,
      color: "text-blue-600 dark:text-blue-400",
      bgColor: "bg-blue-50 dark:bg-blue-900/20",
      change: "+12%",
    },
    {
      title: "Total Tasks",
      value: stats.totalTasks,
      icon: Calendar,
      color: "text-green-600 dark:text-green-400",
      bgColor: "bg-green-50 dark:bg-green-900/20",
      change: "+8%",
    },
    {
      title: "Active Tasks",
      value: stats.runningTasks,
      icon: Clock,
      color: "text-purple-600 dark:text-purple-400",
      bgColor: "bg-purple-50 dark:bg-purple-900/20",
      change: "+3%",
    },
    {
      title: "Data Chefs",
      value: stats.dataChefs,
      icon: Database,
      color: "text-orange-600 dark:text-orange-400",
      bgColor: "bg-orange-50 dark:bg-orange-900/20",
      change: "+15%",
    },
  ];

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "warning":
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Activity className="h-4 w-4 text-blue-500" />;
    }
  };

  return (
    <div className="p-6">
      {/* Welcome Section with User Profile */}
      <div className="mb-8">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold text-base-content mb-2">
              Welcome back{user ? `, ${user.name.split(' ')[0]}` : ''}!
            </h1>
            <p className="text-base-content/70">
              Overview of your AI model management system
            </p>
          </div>

          {/* User Profile Card */}
          {user && (
            <div className="flex items-center gap-3 bg-base-200 px-4 py-3 rounded-lg">
              {user.picture ? (
                <img
                  src={user.picture}
                  alt={user.name}
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                  <User className="w-5 h-5 text-primary" />
                </div>
              )}
              <div className="text-left">
                <p className="font-semibold text-base-content text-sm">{user.name}</p>
                <p className="text-xs text-base-content/60">{user.email}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className="card bg-base-100 shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <div className="card-body">
                <div className="flex items-center justify-between mb-4">
                  <div
                    className={`p-2 rounded-lg bg-${
                      stat.color.split("-")[1]
                    }/10`}
                  >
                    <Icon className="h-6 w-6" />
                  </div>
                  {/* <div className="badge badge-success gap-1">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    {stat.change}
                  </div> */}
                </div>
                <div>
                  <p className="text-2xl font-bold text-base-content mb-1">
                    {stat.value}
                  </p>
                  <p className="text-sm text-base-content/70">{stat.title}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="card bg-base-100 shadow-sm">
          <div className="card-body">
            <h2 className="card-title text-base-content mb-4">
              Recent Activity
            </h2>
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-center space-x-3 p-3 rounded-lg bg-base-200"
                >
                  {getActivityIcon(activity.type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-base-content">
                      {activity.action}
                    </p>
                    <p className="text-xs text-base-content/50">
                      {activity.time}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="card bg-base-100 shadow-sm">
          <div className="card-body">
            <h2 className="card-title text-base-content mb-4 flex items-center justify-between">
              <span>Server Health</span>
              <button
                onClick={checkServerHealth}
                className="btn btn-ghost btn-xs"
              >
                Refresh
              </button>
            </h2>
            <div className="space-y-4">
              {serverHealth.map((server) => (
                <div
                  key={server.name}
                  className={`flex items-center justify-between p-3 rounded-lg ${
                    server.status === 'healthy'
                      ? 'bg-success/10'
                      : 'bg-error/10'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Server className={`h-5 w-5 ${
                      server.status === 'healthy'
                        ? 'text-success'
                        : 'text-error'
                    }`} />
                    <div>
                      <span className="text-sm font-medium text-base-content block">
                        {server.name}
                      </span>
                      {server.responseTime && (
                        <span className="text-xs text-base-content/60">
                          {server.responseTime}ms
                        </span>
                      )}
                    </div>
                  </div>
                  {server.status === 'healthy' ? (
                    <span className="badge badge-success badge-sm">
                      Healthy
                    </span>
                  ) : (
                    <div className="text-right">
                      <span className="badge badge-error badge-sm block mb-1">
                        Unhealthy
                      </span>
                      {server.error && (
                        <span className="text-xs text-error/70">
                          {server.error}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {serverHealth.length === 0 && (
                <div className="text-center py-4 text-base-content/60">
                  <Server className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Checking server status...</p>
                </div>
              )}

              {/* Scheduler Status */}
              {schedulerStatus && (
                <div
                  className={`flex items-center justify-between p-3 rounded-lg mt-4 ${
                    schedulerStatus.is_running
                      ? 'bg-success/10'
                      : 'bg-warning/10'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Clock className={`h-5 w-5 ${
                      schedulerStatus.is_running
                        ? 'text-success'
                        : 'text-warning'
                    }`} />
                    <span className="text-sm font-medium text-base-content">
                      Task Scheduler
                    </span>
                  </div>
                  <span className={`badge badge-sm ${
                    schedulerStatus.is_running
                      ? 'badge-success'
                      : 'badge-warning'
                  }`}>
                    {schedulerStatus.status}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
