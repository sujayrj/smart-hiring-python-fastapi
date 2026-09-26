export function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
      {label}
    </div>
  );
}

export function Page({ title, actions, children }) {
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold tracking-tight">{title}</h1>
        {actions}
      </div>
      {children}
    </div>
  );
}

export function Card({ title, actions, children, className = "" }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <div className="mb-3 flex items-center justify-between">
          {title && <h2 className="text-sm font-bold">{title}</h2>}
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

const BADGE_STYLES = {
  PASS: "bg-green-100 text-green-700",
  PASSED: "bg-green-100 text-green-700",
  SCREENING: "bg-green-100 text-green-700",
  PROMOTED: "bg-green-100 text-green-700",
  ACCEPTED: "bg-green-100 text-green-700",
  COMPLETED: "bg-green-100 text-green-700",
  ACTIVE: "bg-green-100 text-green-700",
  HIRE: "bg-green-100 text-green-700",
  ARCHIVED: "bg-slate-100 text-slate-600",
  APPLIED: "bg-slate-100 text-slate-600",
  FILTERED: "bg-slate-100 text-slate-600",
  DRAFT: "bg-slate-100 text-slate-600",
  REJECT: "bg-red-100 text-red-700",
  REJECTED: "bg-red-100 text-red-700",
  HOLD: "bg-amber-100 text-amber-700",
  ON_HOLD: "bg-amber-100 text-amber-700",
  NO_SHOW: "bg-red-100 text-red-700",
  QA_DONE: "bg-blue-100 text-blue-700",
  INTERVIEW: "bg-indigo-100 text-indigo-700",
  SCHEDULED: "bg-blue-100 text-blue-700",
  DECIDED: "bg-indigo-100 text-indigo-700",
  ADMIN: "bg-indigo-100 text-indigo-700",
  CANDIDATE: "bg-blue-100 text-blue-700",
  INTERVIEWER: "bg-green-100 text-green-700",
};

const STATUS_LABELS = {
  APPLIED: "Filtered",
  SCREENING: "Screening",
  PASSED: "Passed",
  HOLD: "Hold",
  REJECTED: "Rejected",
  INTERVIEW: "Interview scheduled",
  ACCEPTED: "Accepted",
  ON_HOLD: "On-Hold",
  NO_SHOW: "No-show",
  ARCHIVED: "Archived",
  SCHEDULED: "Scheduled",
  COMPLETED: "Completed",
};

export const labelForStatus = (value) => STATUS_LABELS[value] || value;

export function Badge({ value, tone }) {
  const key = tone || String(value || "").toUpperCase();
  const style = BADGE_STYLES[key] || "bg-slate-100 text-slate-600";
  return <span className={`badge ${style}`}>{value}</span>;
}

export function StatusBadge({ value }) {
  return <Badge value={labelForStatus(value)} tone={value} />;
}

const FLAG_LABELS = {
  LOW_RESUME_CONFIDENCE: "low-confidence",
  LOW_QA_CONFIDENCE: "low-confidence",
  SCORE_DISAGREEMENT: "score-disagreement",
  ANTI_CHEAT_TAB_SWITCH: "tab-switching",
  ANTI_CHEAT_COPY_QUESTION: "question-copying",
  ANTI_CHEAT_PASTE: "pasting",
};

export function FlagChip({ type }) {
  return <span className="badge bg-amber-100 text-amber-700">⚑ {FLAG_LABELS[type] || type}</span>;
}

export function Modal({ title, onClose, children, footer }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div className="w-full max-w-xl overflow-hidden rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h3 className="font-bold">{title}</h3>
          <button onClick={onClose} className="text-sm text-slate-400 hover:text-slate-600">
            Esc to close
          </button>
        </div>
        <div className="p-5">{children}</div>
        {footer && (
          <div className="flex justify-end gap-2 border-t border-slate-200 bg-slate-50 px-5 py-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

export function Toast({ toast, onClose }) {
  if (!toast) return null;
  return (
    <div className="fixed bottom-6 right-6 z-[60] flex items-center gap-3 rounded-xl bg-slate-900 px-4 py-3 text-sm text-white shadow-2xl">
      <span>{toast}</span>
      <button className="text-slate-400 hover:text-white" onClick={onClose}>
        ✕
      </button>
    </div>
  );
}

export function ErrorBanner({ error }) {
  if (!error) return null;
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
      {String(error)}
    </div>
  );
}