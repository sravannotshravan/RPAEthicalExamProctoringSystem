# Ethical Online Coding Examination System (POC)

A lightweight, independent full-stack proof-of-concept (POC) that simulates an **ethical online coding examination platform** with a **computer-vision monitoring prototype** powered by OpenCV, a student coding test environment, mock sandbox execution, incident logging, and a faculty oversight dashboard.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Ethical Design Principles](#ethical-design-principles)
3. [Architecture & Tech Stack](#architecture--tech-stack)
4. [Project Structure](#project-structure)
5. [Quick Start Installation](#quick-start-installation)
6. [Database Setup & Seeding](#database-setup--seeding)
7. [Running the Application](#running-the-application)
8. [End-to-End User Flow](#end-to-end-user-flow)
9. [REST API Reference](#rest-api-reference)
10. [Automated Test Suite](#automated-test-suite)
11. [POC Limitations](#poc-limitations)
12. [Future UiPath Integration Roadmap](#future-uipath-integration-roadmap)

---

## Project Overview

This application serves as an initial architecture proof-of-concept for an academic examination platform. It validates the data models, proctoring telemetry pipeline, and human-in-the-loop review workflow prior to integrating robotic process automation (UiPath) or heavyweight cloud infrastructure.

### Key Capabilities
* **Student Test Environment:** Candidate selection, privacy disclosure and consent, split-view coding test interface, live countdown timer, and answer submission.
* **OpenCV CV Monitoring:** Real-time client-to-server visual environment checks using a lightweight pretrained Haar Cascade face detector (`cv2.data.haarcascades`).
* **Ethical Incident Logging:** Automated logging of visual anomalies (`NO_FACE`, `MULTIPLE_FACES`) with debouncing and severity ratings. Candidates are **never** labeled as "cheating."
* **Faculty Oversight Dashboard:** Examination CRUD, question builder, student directory, session logs, and human-in-the-loop review controls (`PENDING`, `REVIEWED`, `DISMISSED`).
* **Mock Execution Sandbox:** Safe simulation of code execution and test evaluation without running untrusted code on the server.

---

## Ethical Design Principles

This prototype is built upon ethical academic proctoring principles:
1. **Transparency & Informed Consent:** Before any session begins, candidates review a clear disclosure detailing what the system checks (presence/multiplicity of faces) and what it **never** does.
2. **No Continuous Video Storage:** Video frames captured by the webcam are processed in-memory by OpenCV for face counting and immediately discarded. No video streams or raw footage are persisted to the database or filesystem.
3. **No Biometrics or Identity Profiling:** The system does not extract biometric facial embeddings, perform facial recognition, or track gaze/eyes.
4. **Human-in-the-Loop Review:** Automated CV outputs are treated as neutral observations ("Anomaly", "Visual Event", "Requires Review"). Academic consequences require human faculty verification.

---

## Architecture & Tech Stack

* **Backend:** Python 3.12+ / 3.13+, Flask 3.x, Flask-SQLAlchemy 3.x
* **Database:** SQLite with SQLAlchemy ORM
* **Computer Vision:** OpenCV (`opencv-python-headless` with Haar Cascade frontal face detector)
* **Frontend:** Semantic HTML5, Vanilla CSS, Bootstrap 5.3, Bootstrap Icons, Vanilla JavaScript
* **Testing:** Pytest 8.x (in-memory SQLite test fixtures)

---

## Project Structure

```text
POCEthicalExamProctoring/
│
├── app/
│   ├── __init__.py              # Flask app factory and blueprint registration
│   ├── models.py                # SQLAlchemy ORM models (Student, Exam, Question, Session, Submission, Incident)
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py               # REST API endpoints (UiPath ready)
│   │   ├── monitoring.py        # CV frame analysis & incident debouncing
│   │   ├── student.py           # Student portal views (selection, consent, exam, completion)
│   │   └── faculty.py           # Faculty views (dashboard, exam/question CRUD, session audit)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cv_monitor.py        # OpenCV face counting & classification service
│   │   ├── audio_monitor.py     # In-memory audio energy / speech classification
│   │   └── code_runner.py       # Mock code execution & sandbox simulator
│   │
│   ├── templates/
│   │   ├── base.html            # Core layout with Bootstrap 5
│   │   ├── student/
│   │   │   ├── select.html      # Candidate & exam selection
│   │   │   ├── consent.html     # Ethical Privacy Notice
│   │   │   ├── exam.html        # Interactive coding workspace & webcam feed
│   │   │   └── completed.html   # Final submission confirmation
│   │   └── faculty/
│   │       ├── dashboard.html   # Oversight dashboard with metric cards
│   │       ├── exams.html       # Exam management
│   │       ├── exam_detail.html # Exam question manager
│   │       ├── students.html    # Student directory
│   │       ├── sessions.html    # Examination session list
│   │       └── session_detail.html # Session audit & incident review controls
│   │
│   └── static/
│       ├── css/styles.css       # Clean, modern UI refinements
│       └── js/
│           └── exam.js          # Client webcam/audio monitoring, timer, runner & submit logic
│
├── instance/
│   └── exam.db                  # Local SQLite database
│
├── tests/
│   ├── conftest.py              # In-memory test client fixtures
│   ├── test_models.py           # Model and relationship tests
│   ├── test_api.py              # REST API, portal & monitoring route tests
│   ├── test_cv_monitor.py       # OpenCV detector & simulation tests
│   └── test_uipath_api.py       # UiPath service auth, import, report & queue tests
│
├── uipath/ExamProctoring/       # UiPath Studio RPA project (see UiPath section below)
│
├── config.py                    # Application and testing configuration (reads .env)
├── .env                         # Local secrets: UIPATH_API_KEY, SECRET_KEY, ... (not committed)
├── seed.py                      # Database seeding script
├── run.py                       # Application launcher (honours PORT)
├── start.ps1 / start.bat / start.sh   # One-click setup & startup scripts
├── run_proctoring_demo.ps1/.bat # Backend + UiPath robot end-to-end demo launcher
├── demo_uipath_live.py          # Python end-to-end UiPath demo & verification
├── requirements.txt             # Minimal dependencies
├── CLAUDE.md                    # Guidance for Claude Code agents
└── README.md                    # System documentation
```

---

## Quick Start Installation

### 1. Clone or Open Workspace
```bash
cd POCEthicalExamProctoring
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
```

Activate the virtual environment:
* **Windows (PowerShell):**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
* **Windows (Command Prompt):**
  ```cmd
  .\.venv\Scripts\activate.bat
  ```
* **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Database Setup & Seeding

Populate the local SQLite database with demo candidates, an initial examination, and starter coding challenges:

```bash
python seed.py
```

This populates:
* **3 Candidates:** Demo Student 1 (`REG2026001`), Demo Student 2 (`REG2026002`), Demo Student 3 (`REG2026003`).
* **1 Exam:** `Python Fundamentals` (45 Minutes).
* **3 Coding Questions:**
  1. *Reverse a String*
  2. *Count Vowels in a String*
  3. *Two Sum Problem*

---

## Running the Application

### Option A: One-Click Startup Scripts (Recommended)

The startup scripts perform these steps in order:
1. Create `.venv` if it is missing.
2. Install `requirements.txt` when it has changed since the last install, or when a core import fails. The last install is recorded in `.venv\.requirements-installed`.
3. Add `UIPATH_API_KEY` and `SECRET_KEY` to `.env` if either is missing. Existing values are never overwritten. The UiPath key is read from `uipath/ExamProctoring/Data/config.json` so the robot and backend agree.
4. Seed the database if `instance/exam.db` is missing or empty.
5. Optionally run the test suite.
6. Stop with an error if the port is already in use.
7. Boot the server.

* **PowerShell:**
  ```powershell
  .\start.ps1
  .\start.ps1 -Port 5050 -Seed -Test
  ```

* **Windows Command Prompt** (forwards all arguments to `start.ps1`):
  ```cmd
  start.bat
  start.bat -Port 5050 -Test
  ```

* **macOS / Linux / Git Bash:**
  ```bash
  chmod +x start.sh && ./start.sh
  ./start.sh --port 5050 --seed --test
  ```

| PowerShell / CMD | Bash | Effect |
|---|---|---|
| `-Port <n>` | `--port <n>` | Port to serve on (default `5000` or `$PORT`) |
| `-Seed` | `--seed` | Force re-seeding of the demo database |
| `-Test` | `--test` | Run `pytest` first; abort startup if tests fail |
| `-SkipInstall` | `--skip-install` | Skip the dependency check/install step |

### Option B: Manual Execution

```bash
python run.py              # or: PORT=5050 python run.py
```

### Configuration (`.env`)

`config.py` loads `KEY=VALUE` pairs from `.env` at startup. Real environment variables take precedence over `.env`.

| Key | Purpose |
|---|---|
| `UIPATH_API_KEY` | Key required as `X-API-Key` / Bearer token on the UiPath service endpoints. It must match `ApiKey` in `uipath/ExamProctoring/Data/config.json`. If the key is empty, these endpoints accept requests without a key. |
| `SECRET_KEY` | Flask session secret |
| `DATABASE_URL` | Optional SQLAlchemy URI (default `sqlite:///instance/exam.db`) |
| `REPORTS_DIR` | Directory served by `/api/reports/download/<file>` (default `uipath/ExamProctoring/Output`) |

Open your web browser:
* **Student Examination Portal:** [http://127.0.0.1:5000/student](http://127.0.0.1:5000/student)
* **Faculty Oversight Dashboard:** [http://127.0.0.1:5000/faculty](http://127.0.0.1:5000/faculty)
* **API Endpoints:** [http://127.0.0.1:5000/api/exams](http://127.0.0.1:5000/api/exams)

---

## End-to-End User Flow

```text
Faculty
  ↓
Create Exam / Add Questions / Add Students (or use seed.py)
  ↓
Student Portal (http://127.0.0.1:5000/student)
  ↓
Select Candidate & Exam
  ↓
Review Ethical Privacy Notice & Provide Consent
  ↓
Exam Workspace Opens
  ├── Live Countdown Timer
  ├── Monitored Webcam Box (with Face Count Badge)
  ├── Code Editor with Starter Code
  └── Mock Execution Sandbox ("Run Test Cases")
  ↓
Submit Answers
  ↓
CV Anomaly Event (Cover camera or use "Simulate Multiple Faces")
  ↓
Incident Stored in DB with Debouncing
  ↓
Student Clicks "Finish Exam" & Confirms Modal
  ↓
Final Submission Receipt Displayed
  ↓
Faculty Opens Dashboard (http://127.0.0.1:5000/faculty)
  ↓
Faculty Audits Session #, Submissions, Scores & Incidents
  ↓
Faculty updates status (PENDING → REVIEWED / DISMISSED)
```

---

## REST API Reference

All endpoints return JSON responses:

### Examinations
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/exams` | List all examinations |
| `POST` | `/api/exams` | Create a new examination |
| `GET` | `/api/exams/<id>` | Get exam details and questions |
| `PUT` | `/api/exams/<id>` | Update an examination |
| `DELETE` | `/api/exams/<id>` | Delete an examination and its questions |

### Questions
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/exams/<id>/questions` | List questions for an examination |
| `POST` | `/api/exams/<id>/questions` | Add a question to an examination |
| `GET` | `/api/questions/<id>` | Get single question details |
| `PUT` | `/api/questions/<id>` | Update a question |
| `DELETE` | `/api/questions/<id>` | Delete a question |

### Students
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/students` | List all registered students |
| `POST` | `/api/students` | Register a new student |
| `GET` | `/api/students/<id>` | Get student details |
| `PUT` | `/api/students/<id>` | Update student profile |
| `DELETE` | `/api/students/<id>` | Delete student |

### Sessions & Submissions
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/sessions` | List all examination sessions |
| `POST` | `/api/sessions` | Create a test session (`student_id`, `exam_id`) |
| `GET` | `/api/sessions/<id>` | Get session audit, submissions, and incidents |
| `POST` | `/api/sessions/<id>/start` | Start session (logs consent & timestamp) |
| `POST` | `/api/sessions/<id>/finish` | Conclude session |
| `POST` | `/api/code/run` | Run mock test cases without submitting |
| `POST` | `/api/submissions` | Submit code solution for grading |

### Proctoring & Incidents
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/monitor/status` | Monitoring subsystem status and supported simulation keys |
| `POST` | `/api/monitor/analyze` | Analyze a webcam frame (`image`), a `simulation` key, telemetry flags, `face_count`, or an explicit `incident_type` |
| `POST` | `/api/monitor/audio` | Analyze audio metrics (`volume`, `db_level`, `speech_detected`), a base64 `audio` chunk, or a `simulation` key |
| `GET` | `/api/sessions/<id>/incidents` | List incidents for a session |
| `POST` | `/api/incidents` | Manually log an incident |
| `PUT` | `/api/incidents/<id>/status` | Update review status (`PENDING`, `REVIEWED`, `DISMISSED`) |

**Monitoring request rules:**
* Both monitoring endpoints accept a JSON object or form data. Any other JSON body gets a normal response, not a server error.
* Flag values such as `"false"`, `"0"`, `"no"` and `"off"` count as false. This applies to telemetry flags, `speech_detected`, and `force`.
* An incident is stored only when the request includes a `session_id` for a session that is not `COMPLETED`.
* An incident with the same type as one logged for the same session in the last **5 seconds** is not stored again. The response returns the earlier `incident_id`. Pass `force: true` to skip this check.
* Severity is normalized to `LOW`, `MEDIUM`, or `HIGH`. Unrecognized values fall back to the endpoint default.
* A non-numeric `face_count` is ignored rather than rejected.

### UiPath Service Endpoints
Endpoints marked 🔑 require `X-API-Key` (or `Authorization: Bearer <key>`) matching `UIPATH_API_KEY`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend health check (no key needed) |
| `GET` | `/api/sessions/eligible` | Resolve the next eligible candidate session (no key needed) |
| `POST` 🔑 / `GET` | `/api/sessions/<id>/environment-check` | Submit / read an RPA environment scan |
| `GET` 🔑 | `/api/incidents/pending` | Pending incidents for triage |
| `GET` 🔑 | `/api/exams/<id>/report-data` | Aggregated exam data for audit reports |
| `POST` 🔑 | `/api/students/import` | Bulk roster import |
| `GET` | `/api/automation/status` | Recent automation runs for the dashboard (no key needed) |
| `POST` | `/api/automation/trigger` | Queue an automation run (no key needed) |
| `GET` 🔑 | `/api/automation/queue` | Oldest pending run for the robot to claim |
| `POST` 🔑 | `/api/automation/runs/<id>/update` | Robot reports status, logs, report path |
| `GET` | `/api/reports/download/<file>` | Download a generated report (no key needed) |

---

## Automated Test Suite

The project includes an automated test suite verifying models, relationships, REST API endpoints, mock execution, OpenCV classification, and simulation routines using an in-memory SQLite database.

Run tests using pytest:

```bash
pytest -v tests/
pytest -v tests/test_api.py::test_api_exam_crud    # single test
.\start.ps1 -Test                                  # run tests, then start the server if they pass
```

Expected output:
```text
tests/test_api.py::test_api_exam_crud PASSED
tests/test_api.py::test_api_question_crud PASSED
tests/test_api.py::test_api_student_crud PASSED
tests/test_api.py::test_api_session_lifecycle_and_submission PASSED
tests/test_api.py::test_api_incidents_review_lifecycle PASSED
tests/test_api.py::test_student_portal_execute_and_submit PASSED
tests/test_api.py::test_faculty_crud_and_dual_mode PASSED
tests/test_api.py::test_monitoring_routes_and_direct_flags PASSED
tests/test_cv_monitor.py::test_cv_service_direct_classification PASSED
tests/test_cv_monitor.py::test_cv_service_blank_frame_bytes PASSED
tests/test_cv_monitor.py::test_monitor_analyze_endpoint_simulations PASSED
tests/test_models.py::test_create_student PASSED
tests/test_models.py::test_create_exam_with_questions PASSED
tests/test_models.py::test_exam_session_and_submission PASSED
tests/test_models.py::test_incident_creation_and_status PASSED
tests/test_uipath_api.py::test_api_health_endpoint PASSED
tests/test_uipath_api.py::test_uipath_service_auth_enforcement PASSED
tests/test_uipath_api.py::test_environment_check_flagged_with_prohibited_process PASSED
tests/test_uipath_api.py::test_student_import_api PASSED
tests/test_uipath_api.py::test_exam_report_data_api PASSED
tests/test_uipath_api.py::test_automation_queue_and_runs PASSED
==================== 21 passed in 0.97s ====================
```

---

## UiPath RPA Integration

A complete, production-grade **UiPath Studio RPA Project** is implemented in `uipath/ExamProctoring/` to orchestrate administrative and proctoring processes against the Flask backend.

### 1. Workflows Implemented

| Workflow | Path | Purpose |
| :--- | :--- | :--- |
| **Main Orchestrator** | `Main.xaml` | Mode dispatcher routing to child workflows via `Switch(Of String)` |
| **Configuration** | `Workflows/LoadConfiguration.xaml` | Loads endpoints, credentials, and scan parameters from `Data/config.json` |
| **Backend Validator** | `Workflows/ValidateBackend.xaml` | Health check verifying Flask API responsiveness and `X-API-Key` |
| **Environment Check** | `Workflows/EnvironmentVerification.xaml` | Scans OS for prohibited processes (Wireshark, debuggers), checks browser and network |
| **Exam Lifecycle** | `Workflows/ExamLifecycle.xaml` | Resolves candidate sessions, executes pre-checks, and activates test workspaces |
| **Incident Triage** | `Workflows/IncidentProcessing.xaml` | Queries pending OpenCV visual anomalies, categorizing by High/Med/Low severity |
| **Report Generator** | `Workflows/GenerateExamReport.xaml` | Aggregates candidate performance & integrity metrics into an audit CSV |
| **Proctor Administration**| `Workflows/ProctorAdministration.xaml` | Ingests and validates bulk student rosters from `Data/sample_students.csv` |
| **Execution Logger** | `Workflows/LogExecutionSummary.xaml` | Records persistent execution history to `Output/execution_log.txt` |

### 2. Running UiPath Automations

#### Option A: One-Command Live Demonstration
Run the end-to-end Python demo script which automatically starts the backend server, triggers the UiPath Robot in `FULL_DEMO` mode, and validates all deliverables:
```bash
.venv\Scripts\python.exe demo_uipath_live.py
```

#### Option B: In UiPath Studio Desktop
1. Open **UiPath Studio** Desktop.
2. Open `uipath/ExamProctoring/project.json`.
3. Visually inspect workflows in the Workflow Designer.
4. Press **F5** or click **Run**.

#### Option C: UiPath RPA CLI (`uip`)
```powershell
# Validate project files
uip rpa validate --project-dir "uipath\ExamProctoring"

# Build and compile
uip rpa build "uipath\ExamProctoring"

# Execute Full E2E Demo
uip rpa run --file-path Main.xaml --project-dir "uipath\ExamProctoring"

# Execute specific mode
uip rpa run --file-path Main.xaml --input-arguments "in_ExecutionMode=PROCESS_INCIDENTS" --project-dir "uipath\ExamProctoring"
```

#### Option D: Interactive Web Dashboard
1. Start the Flask application: `python run.py`.
2. Visit `http://127.0.0.1:5000/faculty`.
3. Use the **UiPath RPA Proctoring Engine** panel to trigger live automation runs (`Full E2E Demo`, `Environment Check`, `Triage Incidents`, `Generate Audit Report`, `Import Roster`).

---

## POC Limitations & Ethical Boundary

1. **Mock Code Execution:** Candidate code is evaluated via mock unit test simulations rather than raw server shell execution.
2. **Human-in-the-Loop Gate:** All computer-vision anomalies and RPA environment flags require human faculty review before any academic determination.
3. **Privacy by Design:** Video frames are analyzed in-memory and discarded immediately; no raw webcam footage or biometric facial embeddings are ever stored.
