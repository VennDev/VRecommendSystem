import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const CallbackPage: React.FC = () => {
  const { checkAuthStatus } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState<string>("Processing authentication...");

  useEffect(() => {
    const handleCallback = async () => {
      try {
        setStatus("Verifying your session...");

        // Wait a brief moment for cookies to be set
        await new Promise((resolve) => setTimeout(resolve, 800));

        setStatus("Loading your profile...");

        // Check auth status to get full user data from backend
        await checkAuthStatus();

        setStatus("Success! Redirecting to dashboard...");

        // Small delay for smooth UX
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Redirect to dashboard
        navigate("/dashboard", { replace: true });
      } catch (error) {
        console.error("Auth callback error:", error);
        setStatus("Authentication failed. Redirecting to login...");

        // Redirect to login on error
        setTimeout(() => {
          navigate("/login", { replace: true });
        }, 2000);
      }
    };

    handleCallback();
  }, [checkAuthStatus, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/10 to-secondary/10 flex items-center justify-center">
      <div className="text-center max-w-md px-6">
        <div className="loading loading-spinner loading-lg text-primary mb-4"></div>
        <h2 className="text-2xl font-bold text-base-content mb-2">
          Welcome to VRecom
        </h2>
        <p className="text-base-content/70 mb-4">
          {status}
        </p>
        <div className="w-full bg-base-300 rounded-full h-2 overflow-hidden">
          <div className="bg-primary h-2 rounded-full animate-pulse" style={{ width: '70%' }}></div>
        </div>
      </div>
    </div>
  );
};

export default CallbackPage;
