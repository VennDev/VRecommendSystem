import React from "react";

export const LoadingSpinner: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-base-200">
      <div className="text-center">
        <div className="loading loading-spinner loading-lg text-primary"></div>
        <p className="text-base-content/70 mt-4 text-lg">Loading application...</p>
      </div>
    </div>
  );
};
