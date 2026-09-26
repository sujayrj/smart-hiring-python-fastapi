import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../services/api";
import { Badge, Card, ErrorBanner, Page, Spinner, StatusBadge } from "../../components/ui";

export default function Result() {
  const { appId } = useParams();
  const [application, setApplication] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.application(appId).then(setApplication).catch((e) => setError(e.message));
  }, [appId]);

  if (error) return <ErrorBanner error={error} />;
  if (!application) return <Spinner />;

  return (
    <Page title="My Result">
      <Card className="text-center">
        <div className="text-sm text-slate-500">{application.jd_title}</div>
        <div className="my-2 text-4xl font-extrabold text-brand-600">
          {application.band || "PENDING"}
        </div>
        <div className="mb-3">
          <StatusBadge value={application.status} />
        </div>
        <p className="text-sm text-slate-600">
          {application.next_steps || "Your application is under review."}
        </p>
      </Card>

      <Card title="Score breakdown">
        <div className="grid grid-cols-3 gap-4 text-center">
          <Metric label="Résumé" value={application.resume_score} />
          <Metric label="Q&A" value={application.qa_score} />
          <Metric label="Combined" value={application.combined_score} strong />
        </div>
        {application.interviewer_name && (
          <p className="mt-4 text-center text-sm text-slate-600">
            Interviewer: <span className="font-medium">{application.interviewer_name}</span>
            {application.interview_scheduled_at
              ? ` · ${new Date(application.interview_scheduled_at).toLocaleString()}`
              : ""}
          </p>
        )}
        <p className="mx-auto mt-4 max-w-md rounded-lg border border-dashed border-slate-300 bg-slate-50 p-3 text-xs text-slate-500">
          AI justifications and raw evidence are hidden from this view.
        </p>
        <div className="mt-4 text-center">
          <Link to="/candidate" className="btn-ghost">
            Back to status
          </Link>
        </div>
      </Card>
    </Page>
  );
}

function Metric({ label, value, strong }) {
  return (
    <div className={`rounded-xl border border-slate-200 p-4 ${strong ? "bg-brand-50" : ""}`}>
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-extrabold ${strong ? "text-brand-700" : ""}`}>
        {value ?? "—"}
      </div>
    </div>
  );
}