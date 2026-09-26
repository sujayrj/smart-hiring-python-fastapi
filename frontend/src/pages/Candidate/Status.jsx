import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import { Badge, Card, ErrorBanner, Page, Spinner, StatusBadge } from "../../components/ui";

export default function Status() {
  const [apps, setApps] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.myApplications().then(setApps).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorBanner error={error} />;
  if (!apps) return <Spinner />;

  return (
    <Page title="My Application">
      {apps.length === 0 && (
        <Card>
          <p className="text-sm text-slate-500">You have no applications yet.</p>
        </Card>
      )}

      {apps.map((a) => (
        <Card key={a.id}>
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-base font-bold">{a.jd_title}</h2>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                <StatusBadge value={a.status} />
                {a.band && <Badge value={a.band} />}
              </div>
            </div>
            <div className="flex gap-2">
              {a.status === "SCREENING" && (
                <Link to={`/candidate/screening/${a.id}`} className="btn-primary">
                  Start screening Q&amp;A
                </Link>
              )}
              {["PASSED", "HOLD", "REJECTED", "INTERVIEW", "ACCEPTED", "ON_HOLD", "NO_SHOW"].includes(
                a.status
              ) && (
                <Link to={`/candidate/result/${a.id}`} className="btn-ghost">
                  View result
                </Link>
              )}
            </div>
          </div>

          {(a.interview_scheduled_at || a.interviewer_name) && (
            <div className="mt-3 rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-sm text-indigo-800">
              <span className="font-semibold">Interview scheduled:</span>{" "}
              {a.interview_scheduled_at
                ? new Date(a.interview_scheduled_at).toLocaleString()
                : "date pending"}
              {a.interviewer_name ? ` · Interviewer: ${a.interviewer_name}` : ""}
            </div>
          )}

          {a.next_steps && <p className="mt-3 text-sm text-slate-600">{a.next_steps}</p>}
          <p className="mt-2 text-xs text-slate-400">
            AI justifications and raw evidence are never shown here.
          </p>
        </Card>
      ))}
    </Page>
  );
}