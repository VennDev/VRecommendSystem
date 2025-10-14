import { Download, FileText, RefreshCw, Server } from "lucide-react";
import React, { useEffect, useState } from "react";
import { activityLogger, ActivityLog } from "../services/activityLogger";
import { apiService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

interface ServerLog {
    timestamp: string;
    message: string;
    level: string;
    server: string;
    raw: string;
}

const LogsPage: React.FC = () => {
    const { user } = useAuth();
    const [logs, setLogs] = useState<ActivityLog[]>([]);
    const [serverLogs, setServerLogs] = useState<ServerLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [serverLogsLoading, setServerLogsLoading] = useState(true);
    const [filter, setFilter] = useState<string>("all");
    const [serverFilter, setServerFilter] = useState<string>("all");
    const [levelFilter, setLevelFilter] = useState<string>("all");

    useEffect(() => {
        if (user) {
            fetchLogs();
        }
        fetchServerLogs();
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

    const fetchServerLogs = async (server: string = "all") => {
        setServerLogsLoading(true);
        try {
            const response = await apiService.getServerLogs(100, server);
            if (response.data) {
                setServerLogs(response.data?.data || []);
            }
        } catch (error) {
            console.error("Failed to fetch server logs:", error);
        } finally {
            setServerLogsLoading(false);
        }
    };

    const handleServerFilterChange = (server: string) => {
        setServerFilter(server);
        fetchServerLogs(server);
    };

    const isValidJSON = (str: string): boolean => {
        try {
            JSON.parse(str);
            return true;
        } catch {
            return false;
        }
    };

    const formatLogMessage = (log: ServerLog): string => {
        if (isValidJSON(log.message)) {
            try {
                const parsed = JSON.parse(log.message);
                return JSON.stringify(parsed, null, 2);
            } catch {
                return log.message;
            }
        }
        return log.message;
    };

    const filteredServerLogs = serverLogs.filter((log) => {
        if (levelFilter !== "all" && log.level !== levelFilter) return false;
        return true;
    });

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
                <div className="flex gap-2">
                    <button
                        onClick={() => activityLogger.downloadLogsAsFile(user?.id)}
                        className="btn btn-secondary gap-2"
                    >
                        <Download className="h-5 w-5" />
                        <span>Download</span>
                    </button>
                    <button
                        onClick={fetchLogs}
                        className="btn btn-primary gap-2"
                        disabled={loading}
                    >
                        <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
                        <span>Refresh</span>
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="mb-6 flex flex-wrap gap-2">
                <button
                    onClick={() => setFilter("all")}
                    className={`btn btn-sm ${filter === "all" ? "btn-primary" : "btn-ghost"
                        }`}
                >
                    All ({logs.length})
                </button>
                {uniqueActions.map((action) => (
                    <button
                        key={action}
                        onClick={() => setFilter(action)}
                        className={`btn btn-sm ${filter === action ? "btn-primary" : "btn-ghost"
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
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-bold text-base-content">
                        Server Logs
                    </h2>
                    <button
                        onClick={() => fetchServerLogs(serverFilter)}
                        className="btn btn-secondary btn-sm gap-2"
                        disabled={serverLogsLoading}
                    >
                        <RefreshCw className={`h-4 w-4 ${serverLogsLoading ? 'animate-spin' : ''}`} />
                        <span>Refresh</span>
                    </button>
                </div>

                {/* Filters */}
                <div className="mb-4 flex flex-wrap gap-2">
                    <div className="flex gap-2 items-center">
                        <span className="text-sm font-medium text-base-content">Server:</span>
                        <button
                            onClick={() => handleServerFilterChange("all")}
                            className={`btn btn-xs ${serverFilter === "all" ? "btn-primary" : "btn-ghost"}`}
                        >
                            All
                        </button>
                        <button
                            onClick={() => handleServerFilterChange("api_server")}
                            className={`btn btn-xs ${serverFilter === "api_server" ? "btn-primary" : "btn-ghost"}`}
                        >
                            API Server
                        </button>
                        <button
                            onClick={() => handleServerFilterChange("ai_server")}
                            className={`btn btn-xs ${serverFilter === "ai_server" ? "btn-primary" : "btn-ghost"}`}
                        >
                            AI Server
                        </button>
                    </div>

                    <div className="divider divider-horizontal"></div>

                    <div className="flex gap-2 items-center">
                        <span className="text-sm font-medium text-base-content">Level:</span>
                        <button
                            onClick={() => setLevelFilter("all")}
                            className={`btn btn-xs ${levelFilter === "all" ? "btn-primary" : "btn-ghost"}`}
                        >
                            All
                        </button>
                        <button
                            onClick={() => setLevelFilter("INFO")}
                            className={`btn btn-xs ${levelFilter === "INFO" ? "btn-primary" : "btn-ghost"}`}
                        >
                            Info
                        </button>
                        <button
                            onClick={() => setLevelFilter("WARNING")}
                            className={`btn btn-xs ${levelFilter === "WARNING" ? "btn-primary" : "btn-ghost"}`}
                        >
                            Warning
                        </button>
                        <button
                            onClick={() => setLevelFilter("ERROR")}
                            className={`btn btn-xs ${levelFilter === "ERROR" ? "btn-primary" : "btn-ghost"}`}
                        >
                            Error
                        </button>
                    </div>
                </div>

                <div className="card bg-base-100 shadow-sm">
                    <div className="card-body">
                        <h3 className="card-title text-lg flex items-center gap-2 mb-4">
                            <Server className="h-5 w-5" />
                            Server Logs ({filteredServerLogs.length})
                        </h3>

                        {serverLogsLoading ? (
                            <div className="text-center py-8">
                                <div className="loading loading-spinner loading-md"></div>
                                <p className="text-base-content/70 mt-2">Loading server logs...</p>
                            </div>
                        ) : (
                            <>
                                {filteredServerLogs.length > 0 ? (
                                    <div className="overflow-x-auto">
                                        <div className="bg-base-200 rounded-lg p-4 max-h-96 overflow-y-auto">
                                            <div className="font-mono text-xs space-y-2">
                                                {filteredServerLogs.map((log, index) => (
                                                    <div
                                                        key={index}
                                                        className="hover:bg-base-300 px-3 py-2 rounded border-l-4"
                                                        style={{
                                                            borderLeftColor: log.level === 'ERROR' ? '#f87171' :
                                                                           log.level === 'WARNING' ? '#fbbf24' : '#60a5fa'
                                                        }}
                                                    >
                                                        <div className="flex items-center gap-3 mb-1">
                                                            <span
                                                                className={`badge badge-xs ${log.level === 'ERROR'
                                                                    ? 'badge-error'
                                                                    : log.level === 'WARNING'
                                                                        ? 'badge-warning'
                                                                        : 'badge-info'
                                                                    }`}
                                                            >
                                                                {log.level}
                                                            </span>
                                                            <span className="badge badge-xs badge-ghost">
                                                                {log.server}
                                                            </span>
                                                            <span className="text-base-content/60 text-xs">
                                                                {new Date(log.timestamp).toLocaleString()}
                                                            </span>
                                                        </div>
                                                        <div className="text-base-content mt-1">
                                                            {isValidJSON(log.message) ? (
                                                                <details className="cursor-pointer">
                                                                    <summary className="text-primary hover:underline">
                                                                        View JSON
                                                                    </summary>
                                                                    <pre className="text-xs mt-2 p-2 bg-base-300 rounded overflow-x-auto whitespace-pre-wrap">
                                                                        {formatLogMessage(log)}
                                                                    </pre>
                                                                </details>
                                                            ) : (
                                                                <span className="whitespace-pre-wrap break-words">
                                                                    {log.message}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="alert alert-info">
                                        <FileText className="h-5 w-5" />
                                        <div>
                                            <p className="font-semibold">No logs available</p>
                                            <p className="text-sm">
                                                Server is running but no logs have been recorded yet. Logs will appear here when the server processes requests.
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LogsPage;
