import React, { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const CallbackPage: React.FC = () => {
  const { checkAuthStatus } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const handleCallback = async () => {
      // Get user info from URL params (if provided)
      const userId = searchParams.get("user_id");
      const email = searchParams.get("email");

      console.log("Callback received:", { userId, email });

      // Wait a moment for cookies to be set
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Check auth status to get full user data from backend
      await checkAuthStatus();

      // Redirect to dashboard
      navigate("/dashboard", { replace: true });
    };

    handleCallback();
  }, [checkAuthStatus, navigate, searchParams]);

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
