import { Bot, Calendar, Clock, Cpu, Database, FileText, Hop as Home, Shield } from "lucide-react";

export const NAVIGATION_ITEMS = [
  { id: "dashboard", name: "Dashboard", icon: Home },
  { id: "models", name: "Models", icon: Cpu },
  { id: "tasks", name: "Tasks", icon: Calendar },
  { id: "scheduler", name: "Scheduler", icon: Clock },
  { id: "data-chefs", name: "Restaurant Data", icon: Database },
  { id: "logs", name: "Activity Logs", icon: FileText },
] as const;

export const isLocalhost = () => {
  const hostname = window.location.hostname;
  return hostname === "localhost" || hostname === "127.0.0.1";
};

export const ADMIN_NAVIGATION_ITEMS = [
  { id: "super-admin", name: "Super Admin", icon: Shield, localhostOnly: true },
] as const;
