import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../services/api";
import { Badge, Card, ErrorBanner, Page, Spinner } from "../../components/ui";

export default function JDList() {
  const [jds, setJds] = useState(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  function load() {
    api.jds().then(setJds).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  if (error) return <ErrorBanner error={error} />;
  if (!jds) return <Spinner />;

  return (
    <Page
      title="Job Descriptions"
      actions={
        <Link to="/admin/jds/new" className="btn-primary">
          + New Job Description
        </Link>
      }
    >
      <Card>
        <table className="w-full">
          <thead>
            <tr>
              <th className="th">Title</th>
              <th className="th">Location</th>
              <th className="th">Experience</th>
              <th className="th">Weights R / Q&amp;A</th>
              <th className="th">Threshold</th>
              <th className="th">Questions</th>
              <th className="th">Actions</th>
            </tr>
          </thead>
          <tbody>
            {jds.map((jd) => (
              <tr key={jd.id}>
                <td className="td font-semibold">
                  <Link className="hover:text-brand-700" to={`/admin/jds/${jd.id}`}>
                    {jd.title}
                  </Link>
                </td>
                <td className="td">{jd.location}</td>
                <td className="td">{jd.experience_years}</td>
                <td className="td">
                  {jd.weights?.resume ?? 60} / {jd.weights?.qa ?? 40}
                </td>
                <td className="td">{jd.pass_threshold}</td>
                <td className="td">{jd.question_count}</td>
                <td className="td">
                  <div className="flex gap-2">
                    <Link className="btn-ghost btn-sm" to={`/admin/jds/${jd.id}/edit`}>
                      Edit
                    </Link>
                    <button
                      className="btn-primary btn-sm"
                      onClick={() => navigate(`/admin/jds/${jd.id}/screening`)}
                    >
                      Run
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {jds.length === 0 && (
              <tr>
                <td className="td text-slate-400" colSpan={7}>
                  No job descriptions yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </Page>
  );
}
