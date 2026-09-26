import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../services/api";
import { Card, ErrorBanner, Page, Spinner } from "../../components/ui";

const QUESTION_SECONDS = 120;

export default function QAScreening() {
  const { appId } = useParams();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState(null);
  const [index, setIndex] = useState(0);
  const [text, setText] = useState("");
  const [seconds, setSeconds] = useState(QUESTION_SECONDS);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const telemetry = useRef([]);
  const submitted = useRef(false);
  const startedAt = useRef(Date.now());

  useEffect(() => {
    api.questions(appId).then(setQuestions).catch((e) => setError(e.message));
  }, [appId]);

  // Anti-cheat telemetry: tab-switch, paste and question-copy (evidence only).
  useEffect(() => {
    const onVisibility = () => {
      if (document.hidden) telemetry.current.push({ event_type: "visibility_change", details: {} });
    };
    const onPaste = () => telemetry.current.push({ event_type: "paste", details: {} });
    const onCopy = () => telemetry.current.push({ event_type: "copy", details: {} });
    document.addEventListener("visibilitychange", onVisibility);
    document.addEventListener("paste", onPaste);
    document.addEventListener("copy", onCopy);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      document.removeEventListener("paste", onPaste);
      document.removeEventListener("copy", onCopy);
    };
  }, []);

  const current = questions?.[index];

  const submit = useCallback(
    async (timedOut = false) => {
      if (!current || submitted.current) return;
      submitted.current = true;
      setBusy(true);
      setError("");
      const timeSpent = Math.round((Date.now() - startedAt.current) / 1000);
      try {
        await api.submitAnswer(appId, {
          question_id: current.id,
          answer_text: text,
          time_spent_seconds: timeSpent,
          telemetry: telemetry.current,
        });
        telemetry.current = [];
        if (index + 1 < questions.length) {
          submitted.current = false;
          setIndex(index + 1);
        } else {
          navigate(`/candidate/result/${appId}`);
        }
      } catch (e) {
        submitted.current = false;
        setError(e.message);
      } finally {
        setBusy(false);
      }
    },
    [appId, current, index, navigate, questions, text]
  );

  useEffect(() => {
    submitted.current = false;
    setText("");
    setSeconds(QUESTION_SECONDS);
    startedAt.current = Date.now();
  }, [current?.id]);

  useEffect(() => {
    if (!current) return;
    const id = setInterval(() => setSeconds((s) => s - 1), 1000);
    return () => clearInterval(id);
  }, [current?.id]);

  useEffect(() => {
    if (seconds <= 0 && current) submit(true);
  }, [seconds, current, submit]);

  if (error && !questions) return <ErrorBanner error={error} />;
  if (!questions) return <Spinner />;
  if (questions.length === 0) {
    return (
      <Page title="Screening">
        <Card>No questions have been configured for this job.</Card>
      </Page>
    );
  }

  const mm = String((Math.max(seconds, 0) / 60) | 0).padStart(2, "0");
  const ss = String(Math.max(seconds, 0) % 60).padStart(2, "0");
  const progress = Math.round(((index + 1) / questions.length) * 100);

  return (
    <Page title={`Question ${index + 1} of ${questions.length}`}>
      <ErrorBanner error={error} />

      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-500">Timed screening</span>
        <span className="text-2xl font-extrabold tabular-nums text-red-600">
          {mm}:{ss}
        </span>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full rounded-full bg-brand-600" style={{ width: `${progress}%` }} />
      </div>

      <Card>
        <h2 className="mb-3 text-base font-semibold">{current.text}</h2>
        <textarea
          className="input min-h-[160px]"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type your answer…"
        />
        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-slate-500">Auto-submits when the timer reaches 0.</span>
          <button className="btn-primary" onClick={() => submit(false)} disabled={busy}>
            {busy ? "Submitting…" : "Submit answer"}
          </button>
        </div>
      </Card>

      <p className="text-xs text-slate-400">
        Tab switches, paste and copy events are captured for anti-cheat review (admin-only) and
        never used for automatic rejection.
      </p>
    </Page>
  );
}