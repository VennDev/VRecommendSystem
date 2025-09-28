import { Bot, Shield, Zap } from "lucide-react";
import React, { useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { buildAuthUrl, API_ENDPOINTS } from "../config/api";

const LoginPage: React.FC = () => {
  const { login } = useAuth();

  const handleGoogleLogin = () => {
    window.location.href = buildAuthUrl(API_ENDPOINTS.AUTH.LOGIN('google'));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/10 to-secondary/10 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-primary rounded-xl flex items-center justify-center mb-4">
            <Bot className="h-8 w-8 text-primary-content" />
          </div>
          <h2 className="text-3xl font-bold text-base-content">
            AI Model Dashboard
          </h2>
          <p className="mt-2 text-sm text-base-content/70">
            Manage your AI models, tasks, and data pipelines
          </p>
        </div>

        <div className="card bg-base-100 shadow-xl">
          <div className="card-body space-y-6">
            <div className="space-y-4">
              <div className="flex items-center space-x-3 text-base-content/80">
                <Shield className="h-5 w-5 text-success" />
                <span className="text-sm">Secure Google Authentication</span>
              </div>
              <div className="flex items-center space-x-3 text-base-content/80">
                <Zap className="h-5 w-5 text-warning" />
                <span className="text-sm">Real-time Model Management</span>
              </div>
              <div className="flex items-center space-x-3 text-base-content/80">
                <Bot className="h-5 w-5 text-primary" />
                <span className="text-sm">Advanced AI Tools</span>
              </div>
            </div>

            <button
              onClick={handleGoogleLogin}
              className="btn btn-primary w-full text-base font-medium hover:scale-105 transition-transform"
            >
              <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Sign in with Google
            </button>

            <p className="text-xs text-center text-base-content/50">
              By signing in, you agree to our Terms of Service and Privacy
              Policy
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
