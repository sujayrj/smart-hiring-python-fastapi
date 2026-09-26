import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import { Badge, Card, ErrorBanner, Page, Spinner } from "../../components/ui";

export default function InterviewerList() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.assignments().then(setRows).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorBanner error={error} />;
  if (!rows) return <Spinner />;

  return (
    <Page title="Assigned Candidates">
      <Card>
        <table className="w-full">
          <thead>
            <tr>
              <th className="th">Candidate</th>
              <th className="th">Job Description</th>
              <th className="th">Combined</th>
              <th className="th">Band</th>
              <th className="th">Interview</th>
              <th className="th">Decision</th>
              <th className="th"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.application_id}>
                <td className="td font-semibold">{r.candidate_name}</td>
                <td className="td">{r.jd_title}</td>
                <td className="td">{r.combined_score ?? "—"}</td>
                <td className="td">{r.band ? <Badge value={r.band} /> : "—"}</td>
                <td className="td whitespace-nowrap text-slate-500">
                  {r.scheduled_at ? new Date(r.scheduled_at).toLocaleString() : "—"}
                  {r.interview_status && (
                    <span className="ml-2">
                      <Badge value={r.interview_status} />
                    </span>
                  )}
                </td>
                <td className="td">{r.decision || "—"}</td>
                <td className="td">
                  <Link className="btn-primary btn-sm" to={`/interviewer/candidates/${r.candidate_id}`}>
                    Review
                  </Link>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td className="td text-slate-400" colSpan={7}>
                  No candidates assigned to you yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </Page>
  );
}
