import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../services/api";
import { Badge, Card, ErrorBanner, Page, Spinner } from "../../components/ui";

export default function Screening() {
  const { id } = useParams();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const run = useCallback(async () => {
    setBusy(true);
    setError("");
    try {
      setResult(await api.runScreening(id));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }, [id]);

  useEffect(() => {
    run();
  }, [run]);

  return (
    <Page
      title={result ? `Screening · ${result.jd_title}` : "Résumé screening"}
      actions={
        <div className="flex gap-2">
          <Link to={`/admin/jds/${id}`} className="btn-ghost">
            Back
          </Link>
          <button className="btn-primary" onClick={run} disabled={busy}>
            {busy ? "Scoring…" : "Re-run screening"}
          </button>
        </div>
      }
    >
      <ErrorBanner error={error} />

      {busy && (
        <Card>
          <Spinner label="Scoring résumés with the LLM…" />
        </Card>
      )}

      {result && !busy && (
        <>
          <div className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm">
            <span className="badge bg-green-100 text-green-700">Completed</span>{" "}
            {result.scored} scored · {result.promoted} promoted · {result.archived} archived ·{" "}
            {result.errors} errors
          </div>

          <Card>
            <table className="w-full">
              <thead>
                <tr>
                  <th className="th">Candidate</th>
                  <th className="th">Score</th>
                  <th className="th">Confidence</th>
                  <th className="th">Matched skills</th>
                  <th className="th">Gaps</th>
                  <th className="th">Outcome</th>
                </tr>
              </thead>
              <tbody>
                {result.results.map((r) => (
                  <tr key={r.application_id}>
                    <td className="td font-medium">{r.candidate_name}</td>
                    <td className="td">{r.score ?? "—"}</td>
                    <td className="td">{r.confidence ?? "—"}</td>
                    <td className="td">{(r.matched_skills || []).join(", ") || "—"}</td>
                    <td className="td">{(r.gaps || []).join(", ") || "—"}</td>
                    <td className="td">
                      {r.outcome === "ERROR" ? (
                        <span className="badge bg-red-100 text-red-700">ERROR</span>
                      ) : (
                        <Badge value={r.outcome} />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </Page>
  );
}
