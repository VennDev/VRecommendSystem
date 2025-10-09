import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

interface RouteConfig {
  [key: string]: string;
}

const ROUTE_MAP: RouteConfig = {
  '/dashboard': 'dashboard',
  '/models': 'models',
  '/tasks': 'tasks',
  '/scheduler': 'scheduler',
  '/data-chefs': 'data-chefs',
  '/logs': 'logs',
};

export const useRouteHandler = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [activeTab, setActiveTab] = useState(() => {
    return ROUTE_MAP[location.pathname] || 'dashboard';
  });

  useEffect(() => {
    const tab = ROUTE_MAP[location.pathname];
    if (tab) {
      setActiveTab(tab);
    }
  }, [location.pathname]);

  const handleTabChange = (tab: string) => {
    const path = tab === 'dashboard' ? '/dashboard' : `/${tab}`;
    navigate(path);
  };

  return { activeTab, handleTabChange };
};
