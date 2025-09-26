import { AlertCircle, Clock, Play, RotateCcw, Square } from "lucide-react";
import React, { useEffect, useState } from "react";
import { apiService } from "../services/api";

const SchedulerPage: React.FC = () => {
  const [schedulers, setSchedulers] = useState<any[]>([]);
  const [activeTasks, setActiveTasks] = useState<number>(0);
  const [totalRunTasks, setTotalRunTasks] = useState<number>(0);
  const [runtimeScheduler, setRuntimeScheduler] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchSchedulers();
  }, []);

  const fetchSchedulers = async () => {
    try {
      // const response = await apiService.listSchedulers();
      // if (response.data) {
      //   setSchedulers(response.data);
      // }
      const [countResponse, tasksResponse, runtimeResponse] = await Promise.all(
        [
          apiService.getTotalCountRunTasks(),
          apiService.listTasks(),
          apiService.getTaskRuntime(),
        ]
      );

      if (countResponse.data) {
        setTotalRunTasks(countResponse.data.data ? countResponse.data.data : 0);
      }

      if (runtimeResponse.data) {
        setRuntimeScheduler(
          runtimeResponse.data.data ? runtimeResponse.data.data : 0
        );
      }

      if (tasksResponse.data) {
        setActiveTasks(Object.keys(tasksResponse.data || {}).length || 0);
      }
    } catch (error) {
      console.error("Failed to fetch schedulers:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStopScheduler = async () => {
    setActionLoading("stop");
    try {
      const response = await apiService.stopScheduler(30);
      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Scheduler stopped successfully!");
        fetchSchedulers();
      }
    } catch (error) {
      alert("Failed to stop scheduler");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRestartScheduler = async () => {
    setActionLoading("restart");
    try {
      const response = await apiService.restartScheduler(30);
      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Scheduler restarted successfully!");
        fetchSchedulers();
      }
    } catch (error) {
      alert("Failed to restart scheduler");
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="loading loading-spinner loading-lg"></div>
          <p className="text-base-content/70 mt-4">Loading scheduler...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-base-content mb-2">Scheduler</h1>
        <p className="text-base-content/70">
          Monitor and control your task scheduler
        </p>
      </div>

      {/* Scheduler Controls */}
      <div className="card bg-base-100 shadow-sm mb-8">
        <div className="card-body">
          <h2 className="card-title text-base-content mb-4">
            Scheduler Controls
          </h2>
          <div className="flex items-center space-x-4">
            <button
              onClick={handleRestartScheduler}
              disabled={actionLoading === "restart"}
              className="btn btn-success gap-2"
            >
              {actionLoading === "restart" ? (
                <div className="loading loading-spinner loading-sm"></div>
              ) : (
                <RotateCcw className="h-4 w-4" />
              )}
              <span>
                {actionLoading === "restart" ? "Restarting..." : "Restart"}
              </span>
            </button>

            <button
              onClick={handleStopScheduler}
              disabled={actionLoading === "stop"}
              className="btn btn-error gap-2"
            >
              {actionLoading === "stop" ? (
                <div className="loading loading-spinner loading-sm"></div>
              ) : (
                <Square className="h-4 w-4" />
              )}
              <span>{actionLoading === "stop" ? "Stopping..." : "Stop"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* System Metrics */}
      <div className="mt-8 card bg-base-100 shadow-sm">
        <div className="card-body">
          <h2 className="card-title text-base-content mb-4">System Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-success mb-1">
                {activeTasks}
              </div>
              <div className="text-sm text-base-content/70">Active Tasks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-secondary mb-1">
                {totalRunTasks}
              </div>
              <div className="text-sm text-base-content/70">Total Runs</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-accent mb-1">
                {runtimeScheduler}s
              </div>
              <div className="text-sm text-base-content/70">Avg Runtime</div>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts */}
      <div className="mt-8 alert alert-warning">
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-medium">Scheduler Alert</h3>
            <p className="text-sm mt-1">
              Data pipeline scheduler is experiencing delays. Check data source
              connectivity.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SchedulerPage;
