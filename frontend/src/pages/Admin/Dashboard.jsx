import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Badge, Card, ErrorBanner, Page, Spinner } from "../../components/ui";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorBanner error={error} />;
  if (!data) return <Spinner />;

  const stats = [
    ["Job Descriptions", data.jds],
    ["Candidates", data.candidates],
    ["In screening", data.in_screening],
    ["Open flags", data.open_flags],
  ];

  return (
    <Page title="Dashboard">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {stats.map(([label, value]) => (
          <Card key={label}>
            <div className="text-xs font-medium text-slate-500">{label}</div>
            <div className="mt-1 text-3xl font-extrabold tracking-tight">{value}</div>
          </Card>
        ))}
      </div>

      <Card title="Recent screening activity">
        <table className="w-full">
          <thead>
            <tr>
              <th className="th">Candidate</th>
              <th className="th">Job Description</th>
              <th className="th">Résumé</th>
              <th className="th">Q&amp;A</th>
              <th className="th">Combined</th>
              <th className="th">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.recent.map((a) => (
              <tr key={a.id}>
                <td className="td">{a.candidate_name}</td>
                <td className="td">{a.jd_title}</td>
                <td className="td">{a.resume_score ?? "—"}</td>
                <td className="td">{a.qa_score ?? "—"}</td>
                <td className="td">{a.combined_score ?? "—"}</td>
                <td className="td">
                  <Badge value={a.status} />
                </td>
              </tr>
            ))}
            {data.recent.length === 0 && (
              <tr>
                <td className="td text-slate-400" colSpan={6}>
                  No activity yet — run résumé screening from a job description.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </Page>
  );
}
