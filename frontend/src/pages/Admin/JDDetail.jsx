import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../services/api";
import { Badge, Card, ErrorBanner, Page, Spinner } from "../../components/ui";

export default function JDDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [jd, setJd] = useState(null);
  const [apps, setApps] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.jd(id), api.applications()])
      .then(([detail, applications]) => {
        setJd(detail);
        setApps(applications.filter((a) => a.jd_id === Number(id)));
      })
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) return <ErrorBanner error={error} />;
  if (!jd) return <Spinner />;

  return (
    <Page
      title={jd.title}
      actions={
        <div className="flex gap-2">
          <Link to={`/admin/jds/${jd.id}/edit`} className="btn-ghost">
            Edit
          </Link>
          <button className="btn-primary" onClick={() => navigate(`/admin/jds/${jd.id}/screening`)}>
            Run résumé screening
          </button>
        </div>
      }
    >
      <Card>
        <div className="grid gap-3 text-sm md:grid-cols-2">
          <div><span className="text-slate-500">Location:</span> {jd.location}</div>
          <div><span className="text-slate-500">Experience:</span> {jd.experience_years}</div>
          <div><span className="text-slate-500">Education:</span> {jd.education || "—"}</div>
          <div><span className="text-slate-500">Weights:</span> Résumé {jd.weights?.resume}% · Q&amp;A {jd.weights?.qa}%</div>
          <div><span className="text-slate-500">Threshold:</span> {jd.pass_threshold} / 100</div>
          <div><span className="text-slate-500">Confidence cutoff:</span> {jd.confidence_cutoff}</div>
          <div><span className="text-slate-500">Must-have:</span> {jd.must_have}</div>
          <div><span className="text-slate-500">Nice-to-have:</span> {jd.nice_to_have}</div>
          <div><span className="text-slate-500">Summary:</span> {jd.summary}</div>
        </div>
      </Card>

      <Card title={`Questions (${jd.questions.length})`}>
        <ol className="list-decimal space-y-2 pl-5 text-sm">
          {jd.questions.map((q) => (
            <li key={q.id}>{q.text}</li>
          ))}
          {jd.questions.length === 0 && <li className="list-none text-slate-400">No questions defined.</li>}
        </ol>
      </Card>

      <Card title={`Candidates applied (${apps.length})`}>
        <table className="w-full">
          <thead>
            <tr>
              <th className="th">Candidate</th>
              <th className="th">Résumé</th>
              <th className="th">Q&amp;A</th>
              <th className="th">Combined</th>
              <th className="th">Band</th>
              <th className="th">Status</th>
            </tr>
          </thead>
          <tbody>
            {apps.map((a) => (
              <tr key={a.id}>
                <td className="td font-medium">{a.candidate_name}</td>
                <td className="td">{a.resume_score ?? "—"}</td>
                <td className="td">{a.qa_score ?? "—"}</td>
                <td className="td">{a.combined_score ?? "—"}</td>
                <td className="td">{a.band ? <Badge value={a.band} /> : "—"}</td>
                <td className="td"><Badge value={a.status} /></td>
              </tr>
            ))}
            {apps.length === 0 && (
              <tr>
                <td className="td text-slate-400" colSpan={6}>
                  No candidates yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </Page>
  );
}
