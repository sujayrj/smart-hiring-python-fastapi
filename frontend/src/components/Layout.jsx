import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV = {
  ADMIN: [
    { to: "/admin", label: "Dashboard", end: true },
    { to: "/admin/jds", label: "Job Descriptions" },
    { to: "/admin/candidates", label: "Candidates" },
    { to: "/admin/audit", label: "Audit Log" },
  ],
  CANDIDATE: [{ to: "/candidate", label: "My Status", end: true }],
  INTERVIEWER: [{ to: "/interviewer", label: "Assigned Candidates", end: true }],
};

const PORTAL = {
  ADMIN: "Admin Portal",
  CANDIDATE: "Candidate Portal",
  INTERVIEWER: "Interviewer Portal",
};

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const items = NAV[user?.role] || [];

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 text-sm font-extrabold text-white">
            S
          </span>
          <span className="font-bold">SmartHire</span>
          <span className="text-slate-400">/ {PORTAL[user?.role]}</span>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-600">
          <span>{user?.name}</span>
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
            {user?.name?.slice(0, 2).toUpperCase()}
          </span>
          <button
            className="text-slate-400 hover:text-slate-700"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Sign out
          </button>
        </div>
      </header>

      <nav className="flex h-12 items-center gap-1 border-b border-slate-200 bg-white px-4">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `rounded-lg px-3 py-1.5 text-sm ${
                isActive ? "bg-brand-50 font-semibold text-brand-700" : "text-slate-600 hover:bg-slate-50"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <main className="mx-auto max-w-6xl px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}
