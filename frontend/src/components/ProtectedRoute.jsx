import { Navigate, Outlet } from "react-router-dom";
import { homeFor, useAuth } from "../context/AuthContext";
import { Spinner } from "./ui";

export default function ProtectedRoute({ role }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner label="Signing in…" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to={homeFor(user.role)} replace />;
  return <Outlet />;
}
