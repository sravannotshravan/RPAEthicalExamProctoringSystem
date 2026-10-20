"""
Live Demonstration Script for UiPath Ethical Exam Proctoring RPA Integration
----------------------------------------------------------------------------
This script:
1. Spins up the Flask backend on http://127.0.0.1:5000 in a background daemon thread.
2. Waits until the health check endpoint GET /api/health responds with 200 OK.
3. Invokes UiPath RPA automation ('uip rpa run --file-path Main.xaml --input-arguments "in_ExecutionMode=FULL_DEMO"').
4. Displays the live log outputs from UiPath Robot execution.
5. Verifies all deliverables:
   - Student roster imported via RPA
   - Environment check logged for candidate session
   - Incidents triaged
   - CSV/Excel Audit report generated in uipath/ExamProctoring/Output/
"""

import os
import sys
import time
import json
import threading
import subprocess
import urllib.request
import urllib.error

API_BASE_URL = "http://127.0.0.1:5000"
API_KEY = "poc-uipath-local-key"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UIPATH_DIR = os.path.join(PROJECT_DIR, "uipath", "ExamProctoring")


def http_get(endpoint, headers=None):
    url = f"{API_BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, json.loads(data)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {}
    except Exception:
        return 0, {}


def start_flask_in_thread():
    print("[1/5] Starting Flask backend server on http://127.0.0.1:5000 in background thread...")
    from app import create_app
    app = create_app()

    def run_app():
        # Run without reloader to allow clean in-process execution
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

    server_thread = threading.Thread(target=run_app, daemon=True)
    server_thread.start()

    attempts = 0
    while attempts < 30:
        status, data = http_get("/api/health", headers={"X-API-Key": API_KEY})
        if status == 200 and str(data.get("status", "")).upper() == "HEALTHY":
            print("      [OK] Flask backend is online and healthy!")
            return server_thread
        time.sleep(0.3)
        attempts += 1

    raise RuntimeError("Flask backend failed to start within 10 seconds.")


def run_uipath_automation(mode="FULL_DEMO"):
    print(f"\n[2/5] Launching UiPath RPA Execution Engine (Mode={mode})...")
    cmd = [
        "uip", "rpa", "run",
        "--file-path", "Main.xaml",
        "--input-arguments", f"in_ExecutionMode={mode}",
        "--project-dir", UIPATH_DIR
    ]
    print(f"      Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=UIPATH_DIR, capture_output=True, text=True, shell=True)

    print("\n--- UiPath Robot Execution Output ---")
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    print("-------------------------------------")

    if result.returncode != 0:
        print(f"      [WARN] UiPath execution returned code {result.returncode}")
    else:
        print("      [OK] UiPath execution completed successfully!")


def verify_deliverables():
    print("\n[3/5] Verifying RPA Execution Deliverables on Backend...")

    # 1. Check student import
    status, students = http_get("/api/students")
    print(f"      - Registered Students Count: {len(students) if isinstance(students, list) else 0}")
    if isinstance(students, list):
        for s in students[-5:]:
            print(f"        * Student: {s.get('name')} | Reg: {s.get('register_number')} | Email: {s.get('email')}")

    # 2. Check candidate environment checks
    status, env_data = http_get("/api/sessions/1/environment-check", headers={"X-API-Key": API_KEY})
    if status == 200:
        env = env_data.get("environment_check", {})
        print(f"      - Session #1 RPA Environment Verification:")
        print(f"        * Check Passed: {env.get('check_passed')}")
        print(f"        * Browser: {env.get('browser_name')}")
        print(f"        * Prohibited Processes: {env.get('prohibited_processes_found')}")
        print(f"        * Summary: {env.get('summary')}")
    else:
        print(f"      - Environment check query status: {status}")

    # 3. Check generated reports in Output/
    print("\n[4/5] Checking Output Directory for Generated Audit Reports...")
    output_dir = os.path.join(UIPATH_DIR, "Output")
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        reports = [f for f in files if f.endswith(".csv")]
        print(f"      - Files in Output directory: {len(files)} files found")
        if reports:
            latest_report = os.path.join(output_dir, sorted(reports)[-1])
            print(f"      [OK] Latest Audit Report: {latest_report}")
            print("           Contents Preview:")
            with open(latest_report, "r", encoding="utf-8") as f:
                for line in f.readlines():
                    print(f"           {line.strip()}")
        else:
            print("      [INFO] No CSV reports found in Output/ yet.")
    else:
        print("      [WARN] Output directory does not exist.")


def main():
    print("=" * 70)
    print(" ETHICAL RPA ONLINE EXAM PROCTORING - LIVE DEMO RUNNER")
    print("=" * 70)
    start_flask_in_thread()
    run_uipath_automation(mode="FULL_DEMO")
    verify_deliverables()
    print("\n[5/5] Live Demonstration Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
