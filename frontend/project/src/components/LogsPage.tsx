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
        </div>
    );
};

export default LogsPage;
