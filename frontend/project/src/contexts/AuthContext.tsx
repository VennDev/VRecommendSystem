import React, {
    createContext,
    ReactNode,
    useContext,
    useEffect,
    useState,
} from "react";
import { buildAuthUrl, API_ENDPOINTS } from "../config/api";
import { activityLogger } from "../services/activityLogger";

interface User {
    id: string;
    email: string;
    name: string;
    picture: string;
    provider: string;
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    login: () => void;
    logout: () => void;
    checkAuthStatus: () => Promise<void>;
    setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Skip auth check for super-admin page (localhost only)
        if (window.location.pathname === "/super-admin") {
            setIsLoading(false);
            return;
        }

        // Try to load user from localStorage first
        const storedUser = localStorage.getItem("user");
        const token = localStorage.getItem("auth_token");

        if (storedUser && token) {
            try {
                // Check if token is expired by verifying with server
                verifyTokenAndLoadUser(storedUser);
            } catch (error) {
                console.error("Failed to parse stored user:", error);
                localStorage.removeItem("user");
                localStorage.removeItem("auth_token");
                setIsLoading(false);
            }
        } else {
            // No stored credentials, check auth status from server
            checkAuthStatus();
        }
    }, []);

    const verifyTokenAndLoadUser = async (storedUser: string) => {
        try {
            const user = JSON.parse(storedUser);
            const token = localStorage.getItem("auth_token");

            if (!token) {
                console.warn("No auth token found, clearing session");
                localStorage.removeItem("user");
                setUser(null);
                setIsLoading(false);
                return;
            }

            // Verify token is still valid by making a simple API call with JWT
            const response = await fetch(
                buildAuthUrl(API_ENDPOINTS.AUTH.CHECK_STATUS),
                {
                    credentials: "include",
                    headers: {
                        Accept: "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                },
            );

            if (response.ok) {
                setUser(user);
            } else {
                console.warn("Token verification failed, clearing session");
                localStorage.removeItem("user");
                localStorage.removeItem("auth_token");
                setUser(null);
            }
        } catch (error) {
            console.error("Token verification error:", error);
            localStorage.removeItem("user");
            localStorage.removeItem("auth_token");
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    const checkAuthStatus = async () => {
        setIsLoading(true);
        try {
            // Check if user and token are stored in localStorage
            const storedUser = localStorage.getItem("user");
            const token = localStorage.getItem("auth_token");

            if (storedUser && token) {
                // User found in localStorage, verify token is still valid
                await verifyTokenAndLoadUser(storedUser);
                return;
            }

            const url = buildAuthUrl(API_ENDPOINTS.AUTH.CHECK_STATUS);
            console.log("Checking auth status at:", url);

            // Try with both JWT token (if available) and session cookies
            const headers: any = {
                Accept: "application/json",
            };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(url, {
                credentials: "include", // Important for session cookies
                headers,
            });

            console.log("Auth check response:", response.status);

            if (response.ok) {
                const data = await response.json();
                console.log("Auth data received:", data);
                if (data.user) {
                    setUser(data.user);
                    localStorage.setItem("user", JSON.stringify(data.user));
                } else {
                    setUser(null);
                    localStorage.removeItem("user");
                    localStorage.removeItem("auth_token");
                }
            } else {
                console.error(
                    "Auth check failed with status:",
                    response.status,
                );
                setUser(null);
                localStorage.removeItem("user");
                localStorage.removeItem("auth_token");
            }
        } catch (error) {
            console.error("Auth check failed:", error);
            setUser(null);
            localStorage.removeItem("user");
            localStorage.removeItem("auth_token");
        } finally {
            setIsLoading(false);
        }
    };

    const login = () => {
        // Redirect to Google OAuth using centralized API config
        window.location.href = buildAuthUrl(API_ENDPOINTS.AUTH.LOGIN("google"));
    };

    const logout = async () => {
        try {
            // Log logout activity before clearing user
            if (user) {
                await activityLogger.log(user.id, user.email, {
                    action: "logout",
                    details: { timestamp: new Date().toISOString() },
                });
            }

            await fetch(buildAuthUrl(API_ENDPOINTS.AUTH.LOGOUT), {
                method: "POST",
                credentials: "include",
            });
            setUser(null);
            localStorage.removeItem("user");
            localStorage.removeItem("auth_token");
            window.location.href = "/login";
        } catch (error) {
            console.error("Logout failed:", error);
            // Still clear user on frontend even if API fails
            setUser(null);
            localStorage.removeItem("user");
            localStorage.removeItem("auth_token");
            window.location.href = "/login";
        }
    };

    return (
        <AuthContext.Provider
            value={{ user, isLoading, login, logout, checkAuthStatus, setUser }}
        >
            {children}
        </AuthContext.Provider>
    );
};
