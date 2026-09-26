import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import {
  Badge,
  Card,
  ErrorBanner,
  FlagChip,
  Page,
  Spinner,
  StatusBadge,
} from "../../components/ui";

export default function CandidateList() {
  const [candidates, setCandidates] = useState(null);
  const [applications, setApplications] = useState([]);
  const [flags, setFlags] = useState([]);
  const [error, setError] = useState("");
  const [sortBy, setSortBy] = useState("combined");
  const [sortDir, setSortDir] = useState("desc");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [jdFilter, setJdFilter] = useState("ALL");

  useEffect(() => {
    Promise.all([api.candidates(), api.applications(), api.flags()])
      .then(([c, a, f]) => {
        setCandidates(c);
        setApplications(a);
        setFlags(f);
      })
      .catch((e) => setError(e.message));
  }, []);

  const rows = useMemo(() => {
    if (!candidates) return [];
    const appFor = (candidateId) => applications.find((a) => a.candidate_id === candidateId);
    let list = candidates.map((c) => ({ candidate: c, app: appFor(c.id) }));

    if (statusFilter !== "ALL") list = list.filter((r) => r.candidate.status === statusFilter);
    if (jdFilter !== "ALL") list = list.filter((r) => r.app?.jd_title === jdFilter);

    const key = {
      combined: (r) => r.app?.combined_score,
      resume: (r) => r.app?.resume_score,
      qa: (r) => r.app?.qa_score,
      confidence: (r) => r.app?.resume_confidence,
      name: (r) => r.candidate.name,
      status: (r) => r.candidate.status,
    }[sortBy];

    list.sort((a, b) => {
      const va = key(a);
      const vb = key(b);
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === "string") return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
      return sortDir === "asc" ? va - vb : vb - va;
    });
    return list;
  }, [candidates, applications, sortBy, sortDir, statusFilter, jdFilter]);

  if (error) return <ErrorBanner error={error} />;
  if (!candidates) return <Spinner />;

  const statuses = ["ALL", ...new Set(candidates.map((c) => c.status))];
  const jds = ["ALL", ...new Set(applications.map((a) => a.jd_title).filter(Boolean))];
  const flagsFor = (applicationId) => flags.filter((f) => f.application_id === applicationId);

  return (
    <Page title="Candidates">
      <Card>
        <div className="mb-4 flex flex-wrap items-end gap-3">
          <div>
            <label className="label">Sort by</label>
            <select className="input" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="combined">Combined score</option>
              <option value="resume">Résumé score</option>
              <option value="qa">Q&amp;A score</option>
              <option value="confidence">Confidence</option>
              <option value="status">Status</option>
              <option value="name">Name</option>
            </select>
          </div>
          <div>
            <label className="label">Direction</label>
            <select className="input" value={sortDir} onChange={(e) => setSortDir(e.target.value)}>
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
          <div>
            <label className="label">Status</label>
            <select
              className="input"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              {statuses.map((s) => (
                <option key={s} value={s}>
                  {s === "ALL" ? "All statuses" : s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Job description</label>
            <select className="input" value={jdFilter} onChange={(e) => setJdFilter(e.target.value)}>
              {jds.map((j) => (
                <option key={j} value={j}>
                  {j === "ALL" ? "All JDs" : j}
                </option>
              ))}
            </select>
          </div>
        </div>

        <table className="w-full">
          <thead>
            <tr>
              <th className="th">Name</th>
              <th className="th">Job Description</th>
              <th className="th">Résumé</th>
              <th className="th">Q&amp;A</th>
              <th className="th">Combined</th>
              <th className="th">Confidence</th>
              <th className="th">Band</th>
              <th className="th">Status</th>
              <th className="th">Flags</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ candidate, app }) => (
              <tr key={candidate.id}>
                <td className="td font-semibold">
                  <Link className="hover:text-brand-700" to={`/admin/candidates/${candidate.id}`}>
                    {candidate.name}
                  </Link>
                </td>
                <td className="td">{app?.jd_title || "—"}</td>
                <td className="td">{app?.resume_score ?? "—"}</td>
                <td className="td">{app?.qa_score ?? "—"}</td>
                <td className="td">{app?.combined_score ?? "—"}</td>
                <td className="td">{app?.resume_confidence ?? "—"}</td>
                <td className="td">{app?.band ? <Badge value={app.band} /> : "—"}</td>
                <td className="td">
                  <StatusBadge value={candidate.status} />
                </td>
                <td className="td">
                  <div className="flex flex-wrap gap-1">
                    {app && flagsFor(app.id).map((f) => <FlagChip key={f.id} type={f.type} />)}
                  </div>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td className="td text-slate-400" colSpan={9}>
                  No candidates match the filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </Page>
  );
}