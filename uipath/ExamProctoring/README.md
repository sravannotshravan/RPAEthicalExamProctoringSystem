# UiPath RPA Ethical Examination Proctoring Engine

This directory contains the production-grade **UiPath Studio RPA Automation Project** integrated into the Ethical Online Examination Proctoring System.

Designed for UiPath Studio Desktop (v26.0+) with `targetFramework: Windows` (Modern .NET) and Visual Basic expressions.

---

## 1. Project Architecture & Workflows

```
uipath/ExamProctoring/
├── project.json                      # UiPath Studio project descriptor & dependencies
├── Main.xaml                         # Central orchestration router (Switch-based mode dispatcher)
├── Data/
│   ├── config.json                   # Runtime endpoint URLs, API credentials & thresholds
│   └── sample_students.csv           # Roster file for bulk student registration
├── Output/
│   ├── execution_log.txt             # Persistent audit log of all automation runs
│   └── Exam_*.csv                    # Generated post-examination audit & proctor reports
└── Workflows/
    ├── LoadConfiguration.xaml        # Resolves settings from config.json & environment variables
    ├── ValidateBackend.xaml          # Health check verifying Flask backend status & API key
    ├── EnvironmentVerification.xaml  # Checks processes, browser, network, media devices
    ├── ExamLifecycle.xaml            # Orchestrates candidate eligibility, pre-check, and session start
    ├── IncidentProcessing.xaml       # Triages pending OpenCV anomalies by severity
    ├── GenerateExamReport.xaml       # Compiles candidate metrics & exports structured CSV audit report
    ├── ProctorAdministration.xaml    # Bulk parses and securely imports student rosters
    └── LogExecutionSummary.xaml      # Formats execution summary banners and appends to audit log
```

---

## 2. Execution Modes

The automation supports multiple execution modes selectable via the `in_ExecutionMode` argument or configured in `Data/config.json`:

| Execution Mode | Description | Invoked Workflow |
| :--- | :--- | :--- |
| `FULL_DEMO` | **(Default)** End-to-end multi-step demonstration: imports roster, verifies candidate environment, starts exam, triages anomalies, generates audit report. | All Workflows |
| `ENVIRONMENT_CHECK` | Scans candidate OS for prohibited processes (e.g. Wireshark, Cheat Engine), validates browser and network, submits to API. | `EnvironmentVerification.xaml` |
| `EXAM_LIFECYCLE` | Resolves eligible exam session, runs pre-checks, and activates the candidate workspace. | `ExamLifecycle.xaml` |
| `PROCESS_INCIDENTS` | Queries pending computer vision anomalies and categorizes them by high, medium, and low severity for faculty review. | `IncidentProcessing.xaml` |
| `GENERATE_REPORT` | Fetches examination telemetry, formats student performance & integrity metrics, and exports an audit CSV. | `GenerateExamReport.xaml` |
| `IMPORT_STUDENTS` | Validates and ingests candidate rosters from `Data/sample_students.csv` into the system. | `ProctorAdministration.xaml` |

---

## 3. How to Run

### Option A: Using UiPath Studio Desktop
1. Launch **UiPath Studio**.
2. Click **Open Project** and navigate to:
   ```
   c:\Users\srava\OneDrive\Documents\POCEthicalExamProctoring\uipath\ExamProctoring\project.json
   ```
3. Inspect `Main.xaml` and child workflows in the visual Workflow Designer.
4. Click **Run** or **Debug** (F5).

### Option B: Using UiPath RPA CLI (`uip`)
Ensure the backend Flask server is running on `http://127.0.0.1:5000`:
```powershell
# Run default Full End-to-End Demo
uip rpa run --file-path Main.xaml

# Run a specific mode (e.g. Incident Triage)
uip rpa run --file-path Main.xaml --input-arguments "in_ExecutionMode=PROCESS_INCIDENTS"

# Run Environment Check for Session #1
uip rpa run --file-path Main.xaml --input-arguments "in_ExecutionMode=ENVIRONMENT_CHECK,in_SessionId=1"

# Validate all workflows
uip rpa validate

# Compile and build package
uip rpa build .
```

### Option C: Using UiRobot CLI (`UiRobot.exe`)
```powershell
& "C:\Users\srava\AppData\Local\Programs\UiPathPlatform\Studio\26.0.204-cloud.25537\UiRobot.exe" execute --file "uipath\ExamProctoring\Main.xaml"
```

---

## 4. API Authentication & Security
- All requests originating from UiPath workflows include the custom authentication header:
  ```http
  X-API-Key: poc-uipath-local-key
  ```
- Endpoints enforce security via the `@require_api_key` Flask decorator, preventing unauthorized manipulation of session or incident data.
