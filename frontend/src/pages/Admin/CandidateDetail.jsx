import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../services/api";
import {
  Badge,
  Card,
  ErrorBanner,
  FlagChip,
  Modal,
  Page,
  Spinner,
  StatusBadge,
  Toast,
} from "../../components/ui";

const TABS = ["Résumé", "Q&A", "AI Evidence", "Flags"];

export default function CandidateDetail() {
  const { id } = useParams();
  const [candidate, setCandidate] = useState(null);
  const [application, setApplication] = useState(null);
  const [interviewers, setInterviewers] = useState([]);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [tab, setTab] = useState("Résumé");
  const [assignOpen, setAssignOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [nextSteps, setNextSteps] = useState("");

  const load = useCallback(async () => {
    try {
      const [cand, apps, people] = await Promise.all([
        api.candidate(id),
        api.applications(),
        api.interviewers(),
      ]);
      setCandidate(cand);
      setInterviewers(people);
      const app = apps.find((a) => a.candidate_id === Number(id));
      if (app) {
        const detail = await api.application(app.id);
        setApplication(detail);
        setNextSteps(detail.next_steps || "");
      }
    } catch (e) {
      setError(e.message);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function saveNextSteps() {
    try {
      await api.setNextSteps(application.id, nextSteps);
      setToast("Next steps saved.");
    } catch (e) {
      setError(e.message);
    }
  }

  async function invite() {
    try {
      const res = await api.invite(application.id);
      setToast(res.message);
    } catch (e) {
      setError(e.message);
    }
  }

  if (error && !candidate) return <ErrorBanner error={error} />;
  if (!candidate) return <Spinner />;

  const evidence = application?.resume_evidence || {};
  const telemetry = application?.telemetry || {};

  return (
    <Page
      title={candidate.name}
      actions={
        <div className="flex gap-2">
          <Link to="/admin/candidates" className="btn-ghost">
            Back
          </Link>
          {application && (
            <button className="btn-primary" onClick={() => setAssignOpen(true)}>
              Assign interviewer
            </button>
          )}
        </div>
      }
    >
      <ErrorBanner error={error} />

      {application && (
        <Card title="Next steps & invitation (admin)">
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              className="input"
              value={nextSteps}
              onChange={(e) => setNextSteps(e.target.value)}
              placeholder="e.g. Technical Round 2, HR discussion"
            />
            <button className="btn-primary" onClick={saveNextSteps}>
              Save
            </button>
            <button className="btn-ghost whitespace-nowrap" onClick={invite}>
              Send invitation
            </button>
          </div>
        </Card>
      )}

      <div className="flex gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm ${
              tab === t
                ? "border-brand-600 font-bold text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Résumé" && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card title="Résumé match">
            <dl className="space-y-2 text-sm">
              <Row k="Score" v={application?.resume_score ?? "—"} />
              <Row k="Confidence" v={application?.resume_confidence ?? "—"} />
              <Row k="Matched skills" v={(evidence.matched_skills || []).join(", ") || "—"} />
              <Row k="Gaps" v={(evidence.gaps || []).join(", ") || "—"} />
              <Row k="Summary" v={evidence.summary || "—"} />
            </dl>
          </Card>
          <Card title="Raw résumé">
            <p className="whitespace-pre-wrap text-sm text-slate-700">{candidate.resume}</p>
          </Card>
        </div>
      )}

      {tab === "Q&A" && (
        <Card title="Per-question scores & timings">
          <table className="w-full">
            <thead>
              <tr>
                <th className="th">Question</th>
                <th className="th">Answer</th>
                <th className="th">Score</th>
                <th className="th">Confidence</th>
                <th className="th">Time</th>
              </tr>
            </thead>
            <tbody>
              {(application?.answers || []).map((a) => (
                <tr key={a.id}>
                  <td className="td">Q{a.question_id}</td>
                  <td className="td text-slate-600">{a.answer_text}</td>
                  <td className="td">{a.score ?? "—"} / 5</td>
                  <td className="td">{a.confidence ?? "—"}</td>
                  <td className="td">
                    {a.time_spent_seconds != null ? `${a.time_spent_seconds}s` : "—"}
                  </td>
                </tr>
              ))}
              {(application?.answers || []).length === 0 && (
                <tr>
                  <td className="td text-slate-400" colSpan={5}>
                    No answers yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      )}

      {tab === "AI Evidence" && (
        <div className="space-y-4">
          <Card title="resume_match">
            <pre className="overflow-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-200">
              {JSON.stringify(evidence, null, 2)}
            </pre>
          </Card>
          <Card title="answer_score (justifications)">
            <div className="space-y-3">
              {(application?.answers || []).map((a) => (
                <div key={a.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                  <div className="font-semibold">
                    Q{a.question_id} — {a.score}/5
                  </div>
                  <div className="text-slate-600">{a.justification || "—"}</div>
                  {a.rubric_hits?.length > 0 && (
                    <div className="mt-1 text-xs text-slate-500">
                      rubric hits: {a.rubric_hits.join(", ")}
                    </div>
                  )}
                </div>
              ))}
              {(application?.answers || []).length === 0 && (
                <p className="text-sm text-slate-400">No evidence yet.</p>
              )}
            </div>
          </Card>
        </div>
      )}

      {tab === "Flags" && (
        <div className="space-y-4">
          <Card title="Anti-cheat telemetry (client-captured)">
            <div className="grid grid-cols-3 gap-4 text-center">
              <Metric label="Tab switches" value={telemetry.tab_switches ?? 0} />
              <Metric label="Pastes" value={telemetry.pastes ?? 0} />
              <Metric label="Question copies" value={telemetry.copies ?? 0} />
            </div>
          </Card>
          <Card title="Confidence / disagreement flags">
            <div className="flex flex-wrap gap-2">
              {(application?.flags || []).map((f) => (
                <div
                  key={f.id}
                  className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm"
                >
                  <FlagChip type={f.type} />
                  <pre className="mt-1 text-xs text-amber-800">{JSON.stringify(f.details)}</pre>
                </div>
              ))}
              {(application?.flags || []).length === 0 && (
                <span className="badge bg-green-100 text-green-700">No flags</span>
              )}
            </div>
          </Card>
        </div>
      )}

      {application?.interview && (
        <Card title="Interview">
          <div className="text-sm">
            Scheduled:{" "}
            {application.interview.scheduled_at
              ? new Date(application.interview.scheduled_at).toLocaleString()
              : "—"}{" "}
            · Status: <StatusBadge value={application.interview.status} /> · Decision:{" "}
            {application.interview.decision || "—"}
            {application.interview.notes && (
              <pre className="mt-2 whitespace-pre-wrap text-xs text-slate-600">
                {application.interview.notes}
              </pre>
            )}
          </div>
        </Card>
      )}

      {application?.band && (
        <p className="text-sm text-slate-500">
          Combined: {application.combined_score ?? "—"} · Band: <Badge value={application.band} />
        </p>
      )}

      {assignOpen && (
        <AssignModal
          applicationId={application.id}
          interviewers={interviewers}
          onClose={() => setAssignOpen(false)}
          onDone={async () => {
            setAssignOpen(false);
            await load();
          }}
          setError={setError}
          busy={busy}
          setBusy={setBusy}
        />
      )}

      <Toast toast={toast} onClose={() => setToast("")} />
    </Page>
  );
}

function Row({ k, v }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-500">{k}</dt>
      <dd className="text-right font-medium">{v}</dd>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 p-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 text-xl font-extrabold">{value}</div>
    </div>
  );
}

function AssignModal({ applicationId, interviewers, onClose, onDone, setError, busy, setBusy }) {
  const [interviewerId, setInterviewerId] = useState(interviewers[0]?.id || "");
  const [when, setWhen] = useState("");
  const [note, setNote] = useState("");

  async function submit() {
    setBusy(true);
    setError("");
    try {
      await api.assignInterviewer(applicationId, {
        interviewer_id: Number(interviewerId),
        scheduled_at: when ? new Date(when).toISOString() : null,
        note,
      });
      await onDone();
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  return (
    <Modal
      title="Assign Interviewer"
      onClose={onClose}
      footer={
        <>
          <button className="btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" onClick={submit} disabled={busy}>
            {busy ? "Assigning…" : "Assign"}
          </button>
        </>
      }
    >
      <div className="space-y-3">
        <div>
          <label className="label">Interviewer</label>
          <select
            className="input"
            value={interviewerId}
            onChange={(e) => setInterviewerId(e.target.value)}
          >
            {interviewers.map((i) => (
              <option key={i.id} value={i.id}>
                {i.name} ({i.username})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Date &amp; time</label>
          <input
            type="datetime-local"
            className="input"
            value={when}
            onChange={(e) => setWhen(e.target.value)}
          />
        </div>
        <div>
          <label className="label">Note to interviewer (optional)</label>
          <input className="input" value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
      </div>
    </Modal>
  );
}