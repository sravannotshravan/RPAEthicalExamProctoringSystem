import json
import pytest
from app.models import db, Student, Exam, ExamSession, Incident, EnvironmentCheck, AutomationRun

def test_api_health_endpoint(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'HEALTHY'
    assert data['database'] == 'CONNECTED'
    assert 'uipath_project_available' in data
    assert 'pending_automation_runs' in data

def test_uipath_service_auth_enforcement(client):
    # Setup session
    stu_res = client.post('/api/students', json={'name': 'Auth Test', 'email': 'auth@test.edu', 'register_number': 'AUTH001'})
    exam_res = client.post('/api/exams', json={'title': 'Auth Exam', 'duration_minutes': 10})
    sess_res = client.post('/api/sessions', json={'student_id': stu_res.get_json()['id'], 'exam_id': exam_res.get_json()['id']})
    session_id = sess_res.get_json()['id']

    # 1. Post without key should fail (401) because TestConfig has UIPATH_API_KEY = 'test-service-key'
    res = client.post(f'/api/sessions/{session_id}/environment-check', json={
        'status': 'PASSED'
    })
    assert res.status_code == 401

    # 2. Post with invalid key should fail (401)
    res = client.post(f'/api/sessions/{session_id}/environment-check', 
                      headers={'X-API-Key': 'wrong-key'},
                      json={'status': 'PASSED'})
    assert res.status_code == 401

    # 3. Post with valid key should succeed (201)
    res = client.post(f'/api/sessions/{session_id}/environment-check', 
                      headers={'X-API-Key': 'test-service-key'},
                      json={
                          'status': 'PASSED',
                          'internet_status': 'OK',
                          'browser_detected': 'chrome.exe',
                          'webcam_status': 'AVAILABLE',
                          'microphone_status': 'AVAILABLE',
                          'summary': 'All checks passed'
                      })
    assert res.status_code == 201
    assert res.get_json()['environment_check']['status'] == 'PASSED'

def test_environment_check_flagged_with_prohibited_process(client):
    stu_res = client.post('/api/students', json={'name': 'Flag Test', 'email': 'flag@test.edu', 'register_number': 'FLAG001'})
    exam_res = client.post('/api/exams', json={'title': 'Flag Exam', 'duration_minutes': 15})
    sess_res = client.post('/api/sessions', json={'student_id': stu_res.get_json()['id'], 'exam_id': exam_res.get_json()['id']})
    session_id = sess_res.get_json()['id']

    # Submit FLAGGED check with prohibited process
    res = client.post(f'/api/sessions/{session_id}/environment-check',
                      headers={'X-API-Key': 'test-service-key'},
                      json={
                          'status': 'FLAGGED',
                          'prohibited_processes': ['wireshark.exe', 'cheatengine.exe'],
                          'summary': 'Prohibited network inspection tool detected'
                      })
    assert res.status_code == 201

    # Verify incident was automatically created as an objective observation
    inc_res = client.get(f'/api/sessions/{session_id}/incidents')
    assert inc_res.status_code == 200
    incidents = inc_res.get_json()
    assert len(incidents) >= 1
    assert incidents[0]['incident_type'] == 'PROHIBITED_PROCESS_DETECTED'
    assert incidents[0]['source'] == 'UiPath'
    assert 'wireshark.exe' in incidents[0]['details']

    # Test idempotency: submitting same check right away should return 200 without creating duplicate incident
    res2 = client.post(f'/api/sessions/{session_id}/environment-check',
                       headers={'X-API-Key': 'test-service-key'},
                       json={
                           'status': 'FLAGGED',
                           'prohibited_processes': 'wireshark.exe, cheatengine.exe',
                           'summary': 'Prohibited network inspection tool detected'
                       })
    assert res2.status_code == 200
    assert 'idempotent' in res2.get_json()['message'].lower()

def test_student_import_api(client):
    # 1. Existing student
    client.post('/api/students', json={'name': 'Existing Stu', 'email': 'exist@test.edu', 'register_number': 'EXIST001'})

    # 2. Batch import with 1 valid, 1 existing duplicate, 1 in-batch duplicate, 1 invalid row
    batch = [
        {'name': 'New Student A', 'email': 'newa@test.edu', 'register_number': 'NEW001'},
        {'name': 'Existing Stu', 'email': 'exist@test.edu', 'register_number': 'OTHER001'},
        {'name': 'Duplicate In Batch', 'email': 'newa@test.edu', 'register_number': 'NEW002'},
        {'name': '', 'email': 'invalid@test.edu', 'register_number': 'INV001'}  # missing name
    ]

    res = client.post('/api/students/import',
                      headers={'X-API-Key': 'test-service-key'},
                      json={'students': batch})
    assert res.status_code in [200, 207]
    data = res.get_json()
    assert data['total_rows'] == 4
    assert data['imported'] == 1
    assert data['skipped'] == 2  # 1 existing + 1 batch dup
    assert data['invalid'] == 1  # 1 missing name

    # Verify newly imported student is in DB
    stu_res = client.get('/api/students')
    names = [s['name'] for s in stu_res.get_json()]
    assert 'New Student A' in names

def test_exam_report_data_api(client):
    exam_res = client.post('/api/exams', json={'title': 'Report Exam', 'duration_minutes': 30})
    exam_id = exam_res.get_json()['id']

    stu_res = client.post('/api/students', json={'name': 'Report Student', 'email': 'rep@test.edu', 'register_number': 'REP001'})
    student_id = stu_res.get_json()['id']

    sess_res = client.post('/api/sessions', json={'student_id': student_id, 'exam_id': exam_id})
    session_id = sess_res.get_json()['id']

    # Fetch report data
    res = client.get(f'/api/exams/{exam_id}/report-data', headers={'X-API-Key': 'test-service-key'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['exam']['id'] == exam_id
    assert 'summary' in data
    assert data['summary']['total_candidates'] == 1
    assert len(data['sessions']) == 1

def test_automation_queue_and_runs(client):
    # Trigger automation
    trig_res = client.post('/api/automation/trigger', json={
        'workflow_name': 'EnvironmentVerification',
        'mode': 'ENVIRONMENT_CHECK'
    })
    assert trig_res.status_code == 202
    run_id = trig_res.get_json()['run']['id']

    # Get from queue
    q_res = client.get('/api/automation/queue', headers={'X-API-Key': 'test-service-key'})
    assert q_res.status_code == 200
    task = q_res.get_json()['task']
    assert task is not None
    assert task['id'] == run_id
    assert task['status'] == 'PENDING'

    # Update run status to RUNNING
    up_res = client.post(f'/api/automation/runs/{run_id}/update',
                         headers={'X-API-Key': 'test-service-key'},
                         json={'status': 'RUNNING', 'log_output': 'Started verification workflow'})
    assert up_res.status_code == 200
    assert up_res.get_json()['run']['status'] == 'RUNNING'

    # Complete run
    done_res = client.post(f'/api/automation/runs/{run_id}/update',
                           headers={'X-API-Key': 'test-service-key'},
                           json={'status': 'COMPLETED', 'log_output': 'Verification passed 100%'})
    assert done_res.status_code == 200
    assert done_res.get_json()['run']['status'] == 'COMPLETED'
