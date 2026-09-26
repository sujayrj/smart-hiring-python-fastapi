import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../../services/api";
import { Card, ErrorBanner, Page, Spinner } from "../../components/ui";

const EMPTY = {
  title: "",
  location: "",
  experience_years: "",
  education: "",
  must_have: "",
  nice_to_have: "",
  summary: "",
  weights: { resume: 60, qa: 40 },
  pass_threshold: 70,
  confidence_cutoff: 0.6,
  questions: [],
};

const csv = (v) =>
  Array.isArray(v) ? v : String(v || "").split(",").map((s) => s.trim()).filter(Boolean);

const bandText = (rubric, key) => {
  if (Array.isArray(rubric)) return key === "score_5" ? rubric.join(", ") : "";
  return (rubric?.[key] || []).join(", ");
};

export default function JDEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const editing = Boolean(id);
  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(editing);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!editing) return;
    api
      .jd(id)
      .then((jd) =>
        setForm({
          ...EMPTY,
          ...jd,
          weights: jd.weights || EMPTY.weights,
          questions: jd.questions || [],
        })
      )
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, editing]);

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const setWeight = (key, value) =>
    setForm((f) => ({ ...f, weights: { ...f.weights, [key]: Number(value) } }));

  const setQuestion = (index, key, value) =>
    setForm((f) => {
      const questions = f.questions.map((q, i) => (i === index ? { ...q, [key]: value } : q));
      return { ...f, questions };
    });

  const addQuestion = () =>
    setForm((f) => ({
      ...f,
      questions: [
        ...f.questions,
        { text: "", reference_answer: "", rubric: { score_5: [], score_3: [], score_0: [] } },
      ],
    }));

  const removeQuestion = (index) =>
    setForm((f) => ({ ...f, questions: f.questions.filter((_, i) => i !== index) }));

  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const payload = {
      ...form,
      pass_threshold: Number(form.pass_threshold),
      confidence_cutoff: Number(form.confidence_cutoff),
      weights: { resume: Number(form.weights.resume), qa: Number(form.weights.qa) },
      questions: form.questions
        .filter((q) => q.text.trim())
        .map((q) => ({
          text: q.text,
          reference_answer: q.reference_answer || "",
          rubric: {
            score_5: csv(q.rubric?.score_5 ?? (Array.isArray(q.rubric) ? q.rubric : [])),
            score_3: csv(q.rubric?.score_3),
            score_0: csv(q.rubric?.score_0),
          },
        })),
    };
    try {
      const saved = editing ? await api.updateJd(id, payload) : await api.createJd(payload);
      navigate(`/admin/jds/${saved.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Spinner />;

  return (
    <Page title={editing ? "Edit Job Description" : "Create Job Description"}>
      <form onSubmit={save} className="space-y-5">
        <ErrorBanner error={error} />

        <Card title="Job details">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="label">Title</label>
              <input className="input" value={form.title} onChange={(e) => set("title", e.target.value)} required />
            </div>
            <div>
              <label className="label">Location</label>
              <input className="input" value={form.location} onChange={(e) => set("location", e.target.value)} />
            </div>
            <div>
              <label className="label">Experience (years)</label>
              <input
                className="input"
                value={form.experience_years}
                onChange={(e) => set("experience_years", e.target.value)}
              />
            </div>
            <div>
              <label className="label">Education</label>
              <input
                className="input"
                value={form.education}
                onChange={(e) => set("education", e.target.value)}
              />
            </div>
            <div>
              <label className="label">Must-have</label>
              <input className="input" value={form.must_have} onChange={(e) => set("must_have", e.target.value)} />
            </div>
            <div>
              <label className="label">Nice-to-have</label>
              <input className="input" value={form.nice_to_have} onChange={(e) => set("nice_to_have", e.target.value)} />
            </div>
            <div>
              <label className="label">Summary</label>
              <input className="input" value={form.summary} onChange={(e) => set("summary", e.target.value)} />
            </div>
          </div>
        </Card>

        <Card title="Scoring configuration">
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="label">Résumé weight (%)</label>
              <input
                type="number"
                className="input"
                value={form.weights.resume}
                onChange={(e) => setWeight("resume", e.target.value)}
              />
            </div>
            <div>
              <label className="label">Q&amp;A weight (%)</label>
              <input
                type="number"
                className="input"
                value={form.weights.qa}
                onChange={(e) => setWeight("qa", e.target.value)}
              />
            </div>
            <div>
              <label className="label">Pass threshold (0-100)</label>
              <input
                type="number"
                className="input"
                value={form.pass_threshold}
                onChange={(e) => set("pass_threshold", e.target.value)}
              />
            </div>
            <div>
              <label className="label">Confidence cutoff</label>
              <input
                type="number"
                step="0.05"
                className="input"
                value={form.confidence_cutoff}
                onChange={(e) => set("confidence_cutoff", e.target.value)}
              />
            </div>
          </div>
        </Card>

        <Card
          title="Screening questions"
          actions={
            <button type="button" className="btn-ghost btn-sm" onClick={addQuestion}>
              + Add question
            </button>
          }
        >
          <div className="space-y-4">
            {form.questions.map((q, index) => (
              <div key={index} className="rounded-xl border border-slate-200 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Question {index + 1}</span>
                  <button
                    type="button"
                    className="text-xs text-red-500 hover:underline"
                    onClick={() => removeQuestion(index)}
                  >
                    Remove
                  </button>
                </div>
                <input
                  className="input mb-2"
                  placeholder="Question text"
                  value={q.text}
                  onChange={(e) => setQuestion(index, "text", e.target.value)}
                />
                <textarea
                  className="input mb-2"
                  placeholder="Reference answer"
                  value={q.reference_answer || ""}
                  onChange={(e) => setQuestion(index, "reference_answer", e.target.value)}
                />
                <input
                  className="input mb-2"
                  placeholder="Rubric score 5 criteria (comma separated)"
                  value={bandText(q.rubric, "score_5")}
                  onChange={(e) =>
                    setQuestion(index, "rubric", {
                      ...(q.rubric || {}),
                      score_5: e.target.value,
                    })
                  }
                />
                <input
                  className="input mb-2"
                  placeholder="Rubric score 3 criteria (comma separated)"
                  value={bandText(q.rubric, "score_3")}
                  onChange={(e) =>
                    setQuestion(index, "rubric", {
                      ...(q.rubric || {}),
                      score_3: e.target.value,
                    })
                  }
                />
                <input
                  className="input"
                  placeholder="Rubric score 0 criteria (comma separated)"
                  value={bandText(q.rubric, "score_0")}
                  onChange={(e) =>
                    setQuestion(index, "rubric", {
                      ...(q.rubric || {}),
                      score_0: e.target.value,
                    })
                  }
                />
              </div>
            ))}
            {form.questions.length === 0 && (
              <p className="text-sm text-slate-400">No questions yet. Add rubric questions for the timed Q&amp;A.</p>
            )}
          </div>
        </Card>

        <div className="flex justify-end gap-2">
          <button type="button" className="btn-ghost" onClick={() => navigate(-1)}>
            Cancel
          </button>
          <button className="btn-primary" disabled={busy}>
            {busy ? "Saving…" : "Save Job Description"}
          </button>
        </div>
      </form>
    </Page>
  );
}
