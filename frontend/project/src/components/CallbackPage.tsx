import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { activityLogger } from "../services/activityLogger";

const CallbackPage: React.FC = () => {
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const [status, setStatus] = useState<string>("Processing authentication...");

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get user data from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const id = urlParams.get("id");
        const email = urlParams.get("email");
        const name = urlParams.get("name");
        const picture = urlParams.get("picture");
        const provider = urlParams.get("provider");
        const token = urlParams.get("token");

        if (!id || !email) {
          throw new Error("Missing user data in callback");
        }

        setStatus("Loading your profile...");

        // Set user data in auth context
        setUser({
          id,
          email,
          name: name || "",
          picture: picture || "",
          provider: provider || "google",
        });

        // Store in localStorage for persistence
        localStorage.setItem("user", JSON.stringify({
          id,
          email,
          name,
          picture,
          provider,
        }));

        // Store JWT token for API authentication
        if (token) {
          localStorage.setItem("auth_token", token);
          console.log("JWT token saved to localStorage");
        } else {
          console.warn("No JWT token received from callback");
        }

        console.log("Auth token in localStorage:", localStorage.getItem("auth_token"));

        // Log successful login activity
        await activityLogger.log(id, email, {
          action: 'login',
          details: {
            provider: provider || 'google',
            name: name || '',
            timestamp: new Date().toISOString(),
          },
        });

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
  }, [setUser, navigate]);

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
