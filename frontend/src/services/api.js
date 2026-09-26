const BASE = import.meta.env.VITE_API_BASE || "/api";

const TOKEN_KEY = "smarthire_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(BASE + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    let message = res.statusText;
    if (data && data.detail) {
      message = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    }
    const error = new Error(message || `Request failed (${res.status})`);
    error.status = res.status;
    throw error;
  }
  return data;
}

export const api = {
  login: (username, password) =>
    request("/login", { method: "POST", body: { username, password }, auth: false }),
  me: () => request("/me"),

  dashboard: () => request("/dashboard"),

  jds: () => request("/jds"),
  jd: (id) => request(`/jds/${id}`),
  createJd: (body) => request("/jds", { method: "POST", body }),
  updateJd: (id, body) => request(`/jds/${id}`, { method: "PUT", body }),
  deleteJd: (id) => request(`/jds/${id}`, { method: "DELETE" }),
  runScreening: (id) => request(`/jds/${id}/resume-score`, { method: "POST" }),

  candidates: () => request("/candidates"),
  candidate: (id) => request(`/candidates/${id}`),

  applications: () => request("/applications"),
  myApplications: () => request("/applications/mine"),
  application: (id) => request(`/applications/${id}`),
  questions: (id) => request(`/applications/${id}/questions`),
  submitAnswer: (id, body) => request(`/applications/${id}/answers`, { method: "POST", body }),
  telemetry: (id, events) =>
    request(`/applications/${id}/telemetry`, { method: "POST", body: events }),
  assignInterviewer: (id, body) =>
    request(`/applications/${id}/assign-interviewer`, { method: "POST", body }),
  recordDecision: (id, body) =>
    request(`/applications/${id}/decision`, { method: "POST", body }),
  addNote: (id, note) => request(`/applications/${id}/notes`, { method: "POST", body: { note } }),
  setNextSteps: (id, next_steps) =>
    request(`/applications/${id}/next-steps`, { method: "POST", body: { next_steps } }),
  invite: (id) => request(`/applications/${id}/invite`, { method: "POST" }),

  audit: () => request("/audit"),
  flags: () => request("/flags"),
  interviewers: () => request("/users/interviewers"),
  assignments: () => request("/interviewer/assignments"),
};
