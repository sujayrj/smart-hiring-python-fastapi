import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login/Login";
import Dashboard from "./pages/Admin/Dashboard";
import JDList from "./pages/Admin/JDList";
import JDEditor from "./pages/Admin/JDEditor";
import JDDetail from "./pages/Admin/JDDetail";
import Screening from "./pages/Admin/Screening";
import CandidateList from "./pages/Admin/CandidateList";
import CandidateDetail from "./pages/Admin/CandidateDetail";
import AuditLog from "./pages/Admin/AuditLog";
import Status from "./pages/Candidate/Status";
import QAScreening from "./pages/Candidate/QAScreening";
import Result from "./pages/Candidate/Result";
import InterviewerList from "./pages/Interviewer/List";
import Review from "./pages/Interviewer/Review";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<ProtectedRoute role="ADMIN" />}>
        <Route path="/admin" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="jds" element={<JDList />} />
          <Route path="jds/new" element={<JDEditor />} />
          <Route path="jds/:id" element={<JDDetail />} />
          <Route path="jds/:id/edit" element={<JDEditor />} />
          <Route path="jds/:id/screening" element={<Screening />} />
          <Route path="candidates" element={<CandidateList />} />
          <Route path="candidates/:id" element={<CandidateDetail />} />
          <Route path="audit" element={<AuditLog />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute role="CANDIDATE" />}>
        <Route path="/candidate" element={<Layout />}>
          <Route index element={<Status />} />
          <Route path="screening/:appId" element={<QAScreening />} />
          <Route path="result/:appId" element={<Result />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute role="INTERVIEWER" />}>
        <Route path="/interviewer" element={<Layout />}>
          <Route index element={<InterviewerList />} />
          <Route path="candidates/:id" element={<Review />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
