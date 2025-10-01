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
    // Try to load user from localStorage first
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
        setIsLoading(false);
        return;
      } catch (error) {
        console.error("Failed to parse stored user:", error);
      }
    }

    // Fall back to checking auth status from server
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    setIsLoading(true);
    try {
      // Check if user is stored in localStorage
      const storedUser = localStorage.getItem("user");
      if (storedUser) {
        setUser(JSON.parse(storedUser));
        setIsLoading(false);
        return;
      }

      const url = buildAuthUrl(API_ENDPOINTS.AUTH.CHECK_STATUS);
      console.log("Checking auth status at:", url);

      const response = await fetch(url, {
        credentials: "include", // Important for session cookies
        headers: {
          'Accept': 'application/json',
        },
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
        }
      } else {
        console.error("Auth check failed with status:", response.status);
        setUser(null);
        localStorage.removeItem("user");
      }
    } catch (error) {
      console.error("Auth check failed:", error);
      setUser(null);
      localStorage.removeItem("user");
    } finally {
      setIsLoading(false);
    }
  };

  const login = () => {
    // Redirect to Google OAuth
    window.location.href = "http://localhost:2030/api/v1/auth/google";
  };

  const logout = async () => {
    try {
      // Log logout activity before clearing user
      if (user) {
        await activityLogger.log(user.id, user.email, {
          action: 'logout',
          details: { timestamp: new Date().toISOString() },
        });
      }

      await fetch(buildAuthUrl(API_ENDPOINTS.AUTH.LOGOUT), {
        method: "POST",
        credentials: "include",
      });
      setUser(null);
      localStorage.removeItem("user");
      window.location.href = "/login";
    } catch (error) {
      console.error("Logout failed:", error);
      // Still clear user on frontend even if API fails
      setUser(null);
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, checkAuthStatus, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};
