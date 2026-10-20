# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A proof-of-concept ethical online coding-exam proctoring system: a Flask + SQLite backend with server-rendered student and faculty portals, OpenCV face-count monitoring, and a UiPath Studio RPA project (`uipath/ExamProctoring/`) that drives the backend through its REST API. The development machine runs Windows, and the virtualenv lives at `.venv\Scripts\python.exe`.

## Commands

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py              # (re)seed instance/exam.db with 3 students, 1 exam, 3 questions
.\.venv\Scripts\python.exe run.py               # dev server on http://127.0.0.1:5000 (PORT env overrides)
.\start.ps1 [-Port 5000] [-Seed] [-Test] [-SkipInstall]   # venv + deps (stamp-based) + .env keys + seed + port check, then runs
                                                # start.bat forwards to start.ps1; start.sh takes --port/--seed/--test/--skip-install

.\.venv\Scripts\python.exe -m pytest -v tests/                                   # full suite
.\.venv\Scripts\python.exe -m pytest tests/test_api.py::test_api_exam_crud -v   # single test

# UiPath side (requires the `uip` CLI / UiPath Robot)
uip rpa validate --project-dir "uipath\ExamProctoring"
uip rpa build "uipath\ExamProctoring"
uip rpa run --file-path Main.xaml --input-arguments "in_ExecutionMode=PROCESS_INCIDENTS" --project-dir "uipath\ExamProctoring"
.\.venv\Scripts\python.exe demo_uipath_live.py  # starts Flask in a thread, runs FULL_DEMO via uip, verifies outputs
.\run_proctoring_demo.ps1 -Mode FULL_DEMO [-NoStudio] [-NoBrowser]
```

The project has no linter or formatter configured.

## Architecture

**App factory** (`app/__init__.py`): `create_app(config_class)` registers four blueprints and runs `db.create_all()` on startup. The project has no migrations: when you change a model in `app/models.py`, delete `instance/exam.db` and re-seed.
- `api_bp` → `/api`: JSON REST for CRUD, sessions, submissions, incidents, and the UiPath integration endpoints.
- `monitoring_bp` → `/api/monitor`: `/analyze` (video frames) and `/audio/analyze`.
- `student_bp` → `/` and `/student/...`: select → consent → exam → completed flow.
- `faculty_bp` → `/faculty`: dashboard, exam/question/student CRUD, session audit, incident review. Many faculty routes do two jobs: they render HTML, or return JSON when `_wants_json()` is true (JSON body, `Accept: application/json`, XHR header, or `?format=json`). They also accept several URL/method aliases (for example `POST /exams/<id>/edit` and `PUT /exams/<id>`). Keep both response paths working when you edit them.

**Domain models**: `Student`, `Exam` → `Question`, `ExamSession` (student × exam) → `Submission` / `Incident` / `EnvironmentCheck`, and `AutomationRun` (UiPath job record). Each model has a `to_dict()` that the API uses for serialization.

**Monitoring pipeline**: `static/js/exam.js` captures webcam frames and POSTs base64 images to `/api/monitor/analyze`. `services/cv_monitor.py` (a Haar-cascade singleton from `get_cv_monitor()`) classifies a frame as NO_FACE, MULTIPLE_FACES, GAZE_SHIFT, PHONE_DETECTED, or similar. The route has two other inputs: a `simulation` key that returns canned results through a large `sim_map`, which the demo buttons and the tests use, and telemetry fields. Before it writes an `Incident`, the route debounces: it skips the write when an incident of the same type was logged for the same session in the last 5 s, unless `force`/`bypass_debounce` is set. `audio_monitor.py` and `/audio/analyze` follow the same pattern.

**Mock code runner**: `services/code_runner.py` never executes submitted code. It returns "Accepted" with a score of 100 unless the code is empty or contains `syntax_error`. Tests rely on this behavior.

**UiPath integration**:
- `require_api_key` in `routes/api.py` protects the robot-facing endpoints: environment-check POST, `incidents/pending`, `exams/<id>/report-data`, `students/import`, `automation/queue`, and `automation/runs/<id>/update`. It checks the `X-API-Key` header or a Bearer token against `UIPATH_API_KEY`, and it is a no-op when that key is empty.
- Automation is queue-based. The faculty dashboard calls `POST /api/automation/trigger`, which creates a PENDING `AutomationRun`. The robot polls `GET /api/automation/queue` and reports progress through `/automation/runs/<id>/update`.
- `Main.xaml` is a `Switch` on `in_ExecutionMode`, which takes one of `FULL_DEMO`, `ENVIRONMENT_CHECK`, `EXAM_LIFECYCLE`, `PROCESS_INCIDENTS`, `GENERATE_REPORT`, or `IMPORT_STUDENTS`. Each case invokes a child workflow from `Workflows/`.
- Robot runtime settings (API base URL, API key, prohibited-process list) live in `uipath/ExamProctoring/Data/config.json`. Reports go to `uipath/ExamProctoring/Output/`, which is also the `REPORTS_DIR` that `/api/reports/download/<file>` serves.
- The demo scripts hardcode the API key `poc-uipath-local-key`. If you change `UIPATH_API_KEY` in `.env`, also update `Data/config.json`, `demo_uipath_live.py`, and `run_proctoring_demo.ps1`.

**Config** (`config.py`): a small built-in loader reads `.env`, and real environment variables take precedence over it. `TestConfig` uses in-memory SQLite, sets `UIPATH_API_KEY='test-service-key'`, and is used by the `app`/`client` fixtures in `tests/conftest.py`. Several settings in `config.py` are not used by any app code yet: `AUTOMATION_LAUNCH_MODE`, `UIROBOT_PATH`, the heartbeat and pickup timeouts, `IMPORT_INBOX_DIR`, and `FACULTY_PASSWORD`. The faculty portal currently has no login. Do not assume these features exist.

## Ethical constraints (product requirements, not style)

- Never persist webcam frames or audio: analyze them in memory and discard them.
- No facial recognition, biometric embeddings, or identity profiling.
- Incidents are neutral observations ("anomaly", "requires review") with status `PENDING` / `REVIEWED` / `DISMISSED`. Never label a candidate as "cheating"; academic outcomes need a human faculty reviewer.

## Repo notes

- The project is not a git repo, and `.gitignore` only excludes `.uipath/.skills/`.
- `.agents/skills/` and `.uipath/.skills/` hold the installed UiPath agent skills (catalog: `.agents/skills/README.md`). Consult them for UiPath/`uip` work, and do not edit them.
- The UiPath README targets Studio 26.0+ with `targetFramework: Windows` and VB expressions.
