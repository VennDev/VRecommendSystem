import { FileText, RefreshCw, Server } from "lucide-react";
import React, { useEffect, useState } from "react";
import { activityLogger } from "../services/activityLogger";
import { useAuth } from "../contexts/AuthContext";

interface ActivityLog {
  id: string;
  user_id: string;
  user_email: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details: Record<string, any>;
  created_at: string;
}

const LogsPage: React.FC = () => {
  const { user } = useAuth();
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    if (user) {
      fetchLogs();
    }
  }, [user]);

  const fetchLogs = async () => {
    if (!user) return;

    setLoading(true);
    try {
      const activityLogs = await activityLogger.getRecentLogs(user.id, 100);
      setLogs(activityLogs);
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter((log) => {
    if (filter === "all") return true;
    return log.action === filter;
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case "login":
        return "badge-success";
      case "logout":
        return "badge-warning";
      case "create":
        return "badge-info";
      case "update":
        return "badge-primary";
      case "delete":
        return "badge-error";
      default:
        return "badge-ghost";
    }
  };

  const uniqueActions = Array.from(new Set(logs.map((log) => log.action)));

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="loading loading-spinner loading-lg"></div>
          <p className="text-base-content/70 mt-4">Loading activity logs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-base-content mb-2">
            Activity Logs
          </h1>
          <p className="text-base-content/70">
            Track your account activity and system operations
          </p>
        </div>
        <button
          onClick={fetchLogs}
          className="btn btn-primary gap-2"
        >
          <RefreshCw className="h-5 w-5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-2">
        <button
          onClick={() => setFilter("all")}
          className={`btn btn-sm ${
            filter === "all" ? "btn-primary" : "btn-ghost"
          }`}
        >
          All ({logs.length})
        </button>
        {uniqueActions.map((action) => (
          <button
            key={action}
            onClick={() => setFilter(action)}
            className={`btn btn-sm ${
              filter === action ? "btn-primary" : "btn-ghost"
            }`}
          >
            {action.charAt(0).toUpperCase() + action.slice(1)} (
            {logs.filter((log) => log.action === action).length})
          </button>
        ))}
      </div>

      {/* Logs List */}
      <div className="card bg-base-100 shadow-sm">
        <div className="card-body">
          <div className="overflow-x-auto">
            <table className="table table-zebra">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>Resource</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="text-sm text-base-content/70">
                      {formatDate(log.created_at)}
                    </td>
                    <td>
                      <span
                        className={`badge ${getActionBadgeColor(log.action)}`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="text-sm">
                      {log.resource_type && (
                        <div>
                          <span className="font-medium">{log.resource_type}</span>
                          {log.resource_id && (
                            <span className="text-base-content/60">
                              {" "}
                              #{log.resource_id}
                            </span>
                          )}
                        </div>
                      )}
                      {!log.resource_type && (
                        <span className="text-base-content/40">-</span>
                      )}
                    </td>
                    <td className="text-sm text-base-content/70">
                      {Object.keys(log.details).length > 0 ? (
                        <details className="cursor-pointer">
                          <summary className="text-primary hover:underline">
                            View details
                          </summary>
                          <pre className="text-xs mt-2 p-2 bg-base-200 rounded overflow-x-auto">
                            {JSON.stringify(log.details, null, 2)}
                          </pre>
                        </details>
                      ) : (
                        <span className="text-base-content/40">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredLogs.length === 0 && (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-base-content/40 mx-auto mb-4" />
              <p className="text-base-content/70 text-lg">No logs found</p>
              <p className="text-base-content/50 text-sm">
                {filter === "all"
                  ? "Start using the system to see activity logs"
                  : `No logs found for action: ${filter}`}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Server Logs Section */}
      <div className="mt-8">
        <h2 className="text-2xl font-bold text-base-content mb-4">
          Server Logs
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card bg-base-100 shadow-sm">
            <div className="card-body">
              <h3 className="card-title text-lg flex items-center gap-2">
                <Server className="h-5 w-5" />
                AI Server Logs
              </h3>
              <p className="text-sm text-base-content/70 mb-4">
                Real-time logs from the AI model training server
              </p>
              <div className="alert alert-info">
                <FileText className="h-5 w-5" />
                <span className="text-sm">
                  Server logs are available on the backend. Check the terminal
                  or log files at <code>backend/ai_server/logs/</code>
                </span>
              </div>
            </div>
          </div>

          <div className="card bg-base-100 shadow-sm">
            <div className="card-body">
              <h3 className="card-title text-lg flex items-center gap-2">
                <Server className="h-5 w-5" />
                API Server Logs
              </h3>
              <p className="text-sm text-base-content/70 mb-4">
                Real-time logs from the API gateway server
              </p>
              <div className="alert alert-info">
                <FileText className="h-5 w-5" />
                <span className="text-sm">
                  Server logs are available on the backend. Check the terminal
                  output or configure logging to a centralized service.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogsPage;
