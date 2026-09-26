"""End-to-end API: auth, roles, screening, Q&A, fusion, interview, admin actions."""

from tests.conftest import auth, login

ADMIN = ("admin1", "admin123")
CANDIDATE = ("candidate1", "cand123")
INTERVIEWER = ("interviewer1", "int123")


def _jd(client, token, title):
    jds = client.get("/api/jds", headers=auth(token)).json()
    return next(j for j in jds if j["title"] == title)


def test_login_rejects_bad_credentials(client):
    resp = client.post("/api/login", json={"username": "admin1", "password": "wrong"})
    assert resp.status_code == 401


def test_seed_loaded_from_input_data(client):
    token = login(client, *ADMIN)
    jds = client.get("/api/jds", headers=auth(token)).json()
    titles = {j["title"] for j in jds}
    assert {"Frontend Developer", "Java Backend Developer", "Python Developer"} <= titles
    # 6 questions per JD and education field present
    frontend = next(j for j in jds if j["title"] == "Frontend Developer")
    assert frontend["question_count"] == 6
    assert frontend["education"]


def test_role_enforcement(client):
    candidate_token = login(client, *CANDIDATE)
    assert client.get("/api/jds", headers=auth(candidate_token)).status_code == 403
    admin_token = login(client, *ADMIN)
    assert client.get("/api/jds", headers=auth(admin_token)).status_code == 200


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_jd_crud(client):
    token = login(client, *ADMIN)
    payload = {
        "title": "Platform Engineer",
        "location": "Remote",
        "experience_years": "2-4",
        "education": "B.E / B.Tech",
        "must_have": "Go, Kubernetes",
        "nice_to_have": "Terraform",
        "weights": {"resume": 50, "qa": 50},
        "pass_threshold": 65,
        "confidence_cutoff": 0.6,
        "summary": "Platform role",
        "questions": [
            {"text": "Explain a pod.", "reference_answer": "unit of scheduling", "rubric": {"score_5": ["scheduling"], "score_3": ["container"], "score_0": ["vm"]}}
        ],
    }
    created = client.post("/api/jds", headers=auth(token), json=payload)
    assert created.status_code == 201, created.text
    jd_id = created.json()["id"]
    assert created.json()["education"] == "B.E / B.Tech"
    assert created.json()["questions"][0]["rubric"]["score_5"] == ["scheduling"]

    updated = client.put(f"/api/jds/{jd_id}", headers=auth(token), json={"pass_threshold": 80})
    assert updated.status_code == 200
    assert updated.json()["pass_threshold"] == 80
    assert client.delete(f"/api/jds/{jd_id}", headers=auth(token)).status_code == 204


def _run_screening_and_qa(client):
    admin = login(client, *ADMIN)
    frontend = _jd(client, admin, "Frontend Developer")
    screening = client.post(f"/api/jds/{frontend['id']}/resume-score", headers=auth(admin))
    assert screening.status_code == 200, screening.text
    assert screening.json()["promoted"] >= 1

    candidate = login(client, *CANDIDATE)
    mine = client.get("/api/applications/mine", headers=auth(candidate)).json()
    app = next(a for a in mine if a["jd_id"] == frontend["id"])
    return admin, candidate, frontend, app


def test_screening_and_qa_flow(client):
    _, candidate, _, app = _run_screening_and_qa(client)
    assert app["status"] == "SCREENING"

    questions = client.get(
        f"/api/applications/{app['id']}/questions", headers=auth(candidate)
    ).json()
    assert len(questions) == 6
    assert "reference_answer" not in questions[0]

    rich_answer = (
        "Virtual DOM is an in-memory tree; React diffs and reconciles and applies minimal "
        "real-DOM updates. Use stable keys, React.memo, virtualization with react-window and "
        "pagination. Context vs Redux selectors. Store JWT in httpOnly cookie; add interceptor. "
        "Box model: content padding border margin and box-sizing border-box; mobile-first with "
        "flex and grid and rem units. Hooks must be top-level only; example useFetch custom hook."
    )
    for q in questions:
        resp = client.post(
            f"/api/applications/{app['id']}/answers",
            headers=auth(candidate),
            json={"question_id": q["id"], "answer_text": rich_answer, "time_spent_seconds": 42},
        )
        assert resp.status_code == 200, resp.text

    detail = client.get(f"/api/applications/{app['id']}", headers=auth(candidate)).json()
    assert detail["qa_score"] is not None
    assert detail["combined_score"] is not None
    assert detail["band"] in ("PASS", "HOLD", "REJECT")
    assert detail["status"] in ("PASSED", "HOLD", "REJECTED")
    assert detail["answers"][0]["time_spent_seconds"] == 42
    assert "reference_answer" not in str(detail)
    assert "justification" not in str(detail)


def test_candidate_cannot_read_other_applications(client):
    admin = login(client, *ADMIN)
    all_apps = client.get("/api/applications", headers=auth(admin)).json()
    candidate = login(client, *CANDIDATE)
    other = next(a for a in all_apps if a["candidate_name"] != "Aarav Sharma")
    assert client.get(f"/api/applications/{other['id']}", headers=auth(candidate)).status_code == 403


def _assign(client, admin, application_id, interviewer_username):
    interviewers = client.get("/api/users/interviewers", headers=auth(admin)).json()
    person = next(u for u in interviewers if u["username"] == interviewer_username)
    resp = client.post(
        f"/api/applications/{application_id}/assign-interviewer",
        headers=auth(admin),
        json={"interviewer_id": person["id"], "scheduled_at": "2026-09-28T10:30:00Z", "note": "Focus on systems."},
    )
    assert resp.status_code == 200, resp.text
    return person


def test_interviewer_sees_only_assigned_and_candidate_sees_interview_info(client):
    admin = login(client, *ADMIN)
    target = client.get("/api/applications", headers=auth(admin)).json()[0]
    _assign(client, admin, target["id"], "interviewer1")

    interviewer = login(client, *INTERVIEWER)
    visible = client.get("/api/candidates", headers=auth(interviewer)).json()
    assert len(visible) == 1
    assert visible[0]["name"] == target["candidate_name"]

    # candidate can see interview date + interviewer name
    candidate_user = next(
        a for a in client.get("/api/applications", headers=auth(admin)).json()
        if a["id"] == target["id"]
    )
    if candidate_user["candidate_id"] == 1:
        cand = login(client, *CANDIDATE)
        mine = client.get("/api/applications/mine", headers=auth(cand)).json()
        assert mine[0]["interview_scheduled_at"] is not None
        assert mine[0]["interviewer_name"]


def test_decision_vocabulary(client):
    admin = login(client, *ADMIN)
    target = client.get("/api/applications", headers=auth(admin)).json()[0]
    _assign(client, admin, target["id"], "interviewer1")
    interviewer = login(client, *INTERVIEWER)

    bad = client.post(
        f"/api/applications/{target['id']}/decision",
        headers=auth(interviewer),
        json={"decision": "HIRE", "notes": "x"},
    )
    assert bad.status_code == 422

    ok = client.post(
        f"/api/applications/{target['id']}/decision",
        headers=auth(interviewer),
        json={"decision": "ACCEPTED", "notes": "Strong."},
    )
    assert ok.status_code == 200, ok.text
    detail = client.get(f"/api/applications/{target['id']}", headers=auth(interviewer)).json()
    assert detail["status"] == "ACCEPTED"
    assert detail["decision"] == "ACCEPTED"


def test_next_steps_and_invitation_stub(client):
    admin = login(client, *ADMIN)
    target = client.get("/api/applications", headers=auth(admin)).json()[0]

    ns = client.post(
        f"/api/applications/{target['id']}/next-steps",
        headers=auth(admin),
        json={"next_steps": "Technical Round 2"},
    )
    assert ns.status_code == 200
    assert ns.json()["next_steps"] == "Technical Round 2"

    invite = client.post(f"/api/applications/{target['id']}/invite", headers=auth(admin))
    assert invite.status_code == 200
    assert "stubbed" in invite.json()["message"].lower()

    events = {e["event_type"] for e in client.get("/api/audit", headers=auth(admin)).json()}
    assert {"next_steps.updated", "invitation.sent"} <= events


def test_telemetry_counters_surface_to_admin(client):
    _, candidate, _, app = _run_screening_and_qa(client)
    payload = [
        {"event_type": "visibility_change", "details": {}},
        {"event_type": "visibility_change", "details": {}},
        {"event_type": "copy", "details": {}},
        {"event_type": "paste", "details": {}},
    ]
    resp = client.post(
        f"/api/applications/{app['id']}/telemetry", headers=auth(candidate), json=payload
    )
    assert resp.status_code == 202

    admin = login(client, *ADMIN)
    detail = client.get(f"/api/applications/{app['id']}", headers=auth(admin)).json()
    assert detail["telemetry"]["tab_switches"] == 2
    assert detail["telemetry"]["copies"] == 1
    assert detail["telemetry"]["pastes"] == 1