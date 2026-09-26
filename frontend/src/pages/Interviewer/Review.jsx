import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../services/api";
import { Badge, Card, ErrorBanner, FlagChip, Modal, Page, Spinner } from "../../components/ui";

const DECISIONS = [
  { value: "ACCEPTED", label: "Accepted" },
  { value: "REJECTED", label: "Rejected" },
  { value: "ON_HOLD", label: "On-Hold" },
  { value: "NO_SHOW", label: "No-show" },
];

export default function Review() {
  const { id } = useParams();
  const [candidate, setCandidate] = useState(null);
  const [application, setApplication] = useState(null);
  const [error, setError] = useState("");
  const [decisionOpen, setDecisionOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [cand, assignments] = await Promise.all([api.candidate(id), api.assignments()]);
      setCandidate(cand);
      const assignment = assignments.find((a) => a.candidate_id === Number(id));
      if (assignment) setApplication(await api.application(assignment.application_id));
    } catch (e) {
      setError(e.message);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorBanner error={error} />;
  if (!candidate) return <Spinner />;

  const evidence = application?.resume_evidence || {};

  return (
    <Page
      title={candidate.name}
      actions={
        <div className="flex gap-2">
          <Link to="/interviewer" className="btn-ghost">
            Back
          </Link>
          {application && (
            <button className="btn-primary" onClick={() => setDecisionOpen(true)}>
              Record decision
            </button>
          )}
        </div>
      }
    >
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Résumé">
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Score</dt><dd>{application?.resume_score ?? "—"} / 100</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Matched</dt><dd>{(evidence.matched_skills || []).join(", ") || "—"}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Gaps</dt><dd>{(evidence.gaps || []).join(", ") || "—"}</dd></div>
          </dl>
        </Card>
        <Card title="Q&A & combined">
          <dl className="space-y-2 text-sm">
            {(application?.answers || []).map((a) => (
              <div key={a.id} className="flex justify-between">
                <dt className="text-slate-500">Q{a.question_id}</dt>
                <dd>{a.score ?? "—"} / 5 ({a.confidence ?? "—"}){a.time_spent_seconds != null ? ` · ${a.time_spent_seconds}s` : ""}</dd>
              </div>
            ))}
            <div className="flex justify-between border-t border-slate-100 pt-2">
              <dt className="text-slate-500">Combined</dt>
              <dd className="font-semibold">
                {application?.combined_score ?? "—"} {application?.band ? <Badge value={application.band} /> : null}
              </dd>
            </div>
          </dl>
        </Card>
      </div>

      <Card title="AI Evidence (authorized reviewers only)">
        <pre className="overflow-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-200">
          {JSON.stringify(evidence, null, 2)}
        </pre>
        <div className="mt-3 flex flex-wrap gap-2">
          {(application?.flags || []).map((f) => (
            <FlagChip key={f.id} type={f.type} />
          ))}
          {(application?.flags || []).length === 0 && (
            <span className="badge bg-green-100 text-green-700">No flags</span>
          )}
        </div>
      </Card>

      <Card title="Anti-cheat telemetry (authorized reviewers only)">
        <div className="grid grid-cols-3 gap-4 text-center">
          <Metric label="Tab switches" value={application?.telemetry?.tab_switches ?? 0} />
          <Metric label="Pastes" value={application?.telemetry?.pastes ?? 0} />
          <Metric label="Question copies" value={application?.telemetry?.copies ?? 0} />
        </div>
      </Card>

      {application?.interview && (
        <Card title="Interview & notes">
          <div className="text-sm">
            Scheduled: {application.interview.scheduled_at || "—"} · Decision:{" "}
            {application.interview.decision || "—"}
          </div>
          {application.interview.notes && (
            <pre className="mt-2 whitespace-pre-wrap text-xs text-slate-600">
              {application.interview.notes}
            </pre>
          )}
        </Card>
      )}

      {decisionOpen && application && (
        <DecisionModal
          applicationId={application.id}
          onClose={() => setDecisionOpen(false)}
          onDone={async () => {
            setDecisionOpen(false);
            await load();
          }}
          setError={setError}
          busy={busy}
          setBusy={setBusy}
        />
      )}
    </Page>
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

function DecisionModal({ applicationId, onClose, onDone, setError, busy, setBusy }) {
  const [decision, setDecision] = useState("ACCEPTED");
  const [notes, setNotes] = useState("");

  async function submit() {
    setBusy(true);
    setError("");
    try {
      await api.recordDecision(applicationId, { decision, notes });
      await onDone();
    } catch (e) {
      setError(e.message);
      setBusy(false);
    }
  }

  return (
    <Modal
      title="Record Interview Decision"
      onClose={onClose}
      footer={
        <>
          <button className="btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" onClick={submit} disabled={busy}>
            {busy ? "Saving…" : "Save decision & notes"}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        <div>
          <label className="label">Decision</label>
          <div className="flex flex-wrap gap-2">
            <div className="flex flex-wrap gap-2">
              {DECISIONS.map((d) => (
                <button
                  key={d.value}
                  onClick={() => setDecision(d.value)}
                  className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                    decision === d.value
                      ? "border-brand-600 bg-brand-600 text-white"
                      : "border-slate-200 bg-white text-slate-600"
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div>
          <label className="label">Notes (timestamped)</label>
          <textarea
            className="input min-h-[100px]"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Interview notes…"
          />
        </div>
      </div>
    </Modal>
  );
}
