import React, { useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";

const CallbackPage: React.FC = () => {
  const { checkAuthStatus } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      // Wait a moment for the backend to process the session
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Check auth status to get user data
      await checkAuthStatus();

      // Redirect to dashboard
      window.location.href = "/dashboard";
    };

    handleCallback();
  }, [checkAuthStatus]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/10 to-secondary/10 flex items-center justify-center">
      <div className="text-center">
        <div className="loading loading-spinner loading-lg text-primary mb-4"></div>
        <h2 className="text-2xl font-bold text-base-content mb-2">
          Completing Sign In...
        </h2>
        <p className="text-base-content/70">
          Please wait while we set up your account
        </p>
      </div>
    </div>
  );
};

export default CallbackPage;
