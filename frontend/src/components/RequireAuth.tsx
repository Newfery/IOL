import { Navigate } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { useAuth } from "@/lib/auth";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth();
  if (!ready) return <div className="min-h-screen bg-background" />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
