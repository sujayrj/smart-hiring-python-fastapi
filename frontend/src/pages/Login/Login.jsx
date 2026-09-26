import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { homeFor, useAuth } from "../../context/AuthContext";
import { ErrorBanner } from "../../components/ui";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin1");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await login(username, password);
      navigate(homeFor(user.role), { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const quick = (u, p) => () => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 via-slate-50 to-cyan-50 p-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl"
      >
        <div className="mb-6 flex flex-col items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-2xl font-extrabold text-white">
            S
          </span>
          <div className="text-center">
            <h1 className="text-xl font-bold">SmartHire</h1>
            <p className="text-xs text-slate-500">AI-powered screening &amp; interview tracking</p>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <label className="label">Username</label>
            <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <ErrorBanner error={error} />
          <button className="btn-primary w-full justify-center" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="mb-2 text-xs text-slate-500">Demo users</p>
          <div className="flex flex-wrap justify-center gap-2">
            <button type="button" className="btn-ghost btn-sm" onClick={quick("admin1", "admin123")}>
              admin
            </button>
            <button
              type="button"
              className="btn-ghost btn-sm"
              onClick={quick("candidate1", "cand123")}
            >
              candidate
            </button>
            <button
              type="button"
              className="btn-ghost btn-sm"
              onClick={quick("interviewer1", "int123")}
            >
              interviewer
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
