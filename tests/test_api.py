import json

def test_api_exam_crud(client):
    # 1. Create Exam
    res = client.post('/api/exams', json={
        'title': 'Operating Systems',
        'description': 'Processes and Threads',
        'duration_minutes': 50
    })
    assert res.status_code == 201
    exam_data = res.get_json()
    exam_id = exam_data['id']
    assert exam_data['title'] == 'Operating Systems'

    # 2. Get Exams List
    res = client.get('/api/exams')
    assert res.status_code == 200
    assert len(res.get_json()) >= 1

    # 3. Get Single Exam
    res = client.get(f'/api/exams/{exam_id}')
    assert res.status_code == 200
    assert res.get_json()['title'] == 'Operating Systems'

    # 4. Update Exam
    res = client.put(f'/api/exams/{exam_id}', json={
        'title': 'Advanced Operating Systems',
        'duration_minutes': 60
    })
    assert res.status_code == 200
    assert res.get_json()['title'] == 'Advanced Operating Systems'
    assert res.get_json()['duration_minutes'] == 60

    # 5. Delete Exam
    res = client.delete(f'/api/exams/{exam_id}')
    assert res.status_code == 200
    res = client.get(f'/api/exams/{exam_id}')
    assert res.status_code == 404

def test_api_question_crud(client):
    # Create Exam first
    exam_res = client.post('/api/exams', json={'title': 'Networks', 'duration_minutes': 30})
    exam_id = exam_res.get_json()['id']

    # Add Question
    res = client.post(f'/api/exams/{exam_id}/questions', json={
        'title': 'Subnet Calculation',
        'description': 'Calculate usable hosts for /24 CIDR',
        'starter_code': 'def calculate(): pass',
        'language': 'python'
    })
    assert res.status_code == 201
    q_id = res.get_json()['id']

    # Get Questions
    res = client.get(f'/api/exams/{exam_id}/questions')
    assert res.status_code == 200
    assert len(res.get_json()) == 1

    # Update Question
    res = client.put(f'/api/questions/{q_id}', json={
        'title': 'Subnet Masks & IP Ranges'
    })
    assert res.status_code == 200
    assert res.get_json()['title'] == 'Subnet Masks & IP Ranges'

    # Delete Question
    res = client.delete(f'/api/questions/{q_id}')
    assert res.status_code == 200

def test_api_student_crud(client):
    # Create Student
    res = client.post('/api/students', json={
        'name': 'Dave Miller',
        'email': 'dave@university.edu',
        'register_number': 'REG501'
    })
    assert res.status_code == 201
    stu_id = res.get_json()['id']

    # Duplicate check
    res = client.post('/api/students', json={
        'name': 'Duplicate',
        'email': 'dave@university.edu',
        'register_number': 'REG502'
    })
    assert res.status_code == 409

    # Get Student
    res = client.get(f'/api/students/{stu_id}')
    assert res.status_code == 200
    assert res.get_json()['name'] == 'Dave Miller'

    # Delete Student
    res = client.delete(f'/api/students/{stu_id}')
    assert res.status_code == 200

def test_api_session_lifecycle_and_submission(client):
    # Setup Student and Exam
    stu_res = client.post('/api/students', json={
        'name': 'Eve Candidate',
        'email': 'eve@test.edu',
        'register_number': 'REG601'
    })
    student_id = stu_res.get_json()['id']

    exam_res = client.post('/api/exams', json={'title': 'Python Logic', 'duration_minutes': 20})
    exam_id = exam_res.get_json()['id']

    q_res = client.post(f'/api/exams/{exam_id}/questions', json={
        'title': 'Palindrome Check',
        'description': 'Check if palindrome',
        'starter_code': 'def is_palindrome(s): pass'
    })
    question_id = q_res.get_json()['id']

    # 1. Create Session
    sess_res = client.post('/api/sessions', json={
        'student_id': student_id,
        'exam_id': exam_id
    })
    assert sess_res.status_code in [200, 201]
    session_id = sess_res.get_json()['id']
    assert sess_res.get_json()['status'] == 'NOT_STARTED'

    # 2. Start Session (records consent)
    start_res = client.post(f'/api/sessions/{session_id}/start')
    assert start_res.status_code == 200
    assert start_res.get_json()['status'] == 'ACTIVE'
    assert start_res.get_json()['consent_given'] is True

    # 3. Test Mock Code Runner
    run_res = client.post('/api/code/run', json={
        'code': 'def is_palindrome(s): return s == s[::-1]',
        'language': 'python',
        'question_id': question_id
    })
    assert run_res.status_code == 200
    assert run_res.get_json()['status'] == 'Accepted'
    assert run_res.get_json()['is_mock'] is True

    # 4. Submit Solution
    sub_res = client.post('/api/submissions', json={
        'session_id': session_id,
        'question_id': question_id,
        'code': 'def is_palindrome(s): return s == s[::-1]',
        'language': 'python'
    })
    assert sub_res.status_code == 201
    assert sub_res.get_json()['score'] == 100

    # 5. Finish Session
    finish_res = client.post(f'/api/sessions/{session_id}/finish')
    assert finish_res.status_code == 200
    assert finish_res.get_json()['status'] == 'COMPLETED'
    assert finish_res.get_json()['ended_at'] is not None

def test_api_incidents_review_lifecycle(client):
    # Setup session
    stu_res = client.post('/api/students', json={'name': 'Frank', 'email': 'frank@test.edu', 'register_number': 'REG701'})
    exam_res = client.post('/api/exams', json={'title': 'Math', 'duration_minutes': 15})
    sess_res = client.post('/api/sessions', json={'student_id': stu_res.get_json()['id'], 'exam_id': exam_res.get_json()['id']})
    session_id = sess_res.get_json()['id']

    # 1. Create Incident
    inc_res = client.post('/api/incidents', json={
        'session_id': session_id,
        'incident_type': 'NO_FACE',
        'severity': 'LOW',
        'source': 'CV',
        'details': 'Candidate moved out of frame'
    })
    assert inc_res.status_code == 201
    incident_id = inc_res.get_json()['id']
    assert inc_res.get_json()['review_status'] == 'PENDING'

    # 2. Get Session Incidents
    list_res = client.get(f'/api/sessions/{session_id}/incidents')
    assert list_res.status_code == 200
    assert len(list_res.get_json()) == 1

    # 3. Update Incident Review Status
    status_res = client.put(f'/api/incidents/{incident_id}/status', json={'status': 'REVIEWED'})
    assert status_res.status_code == 200
    assert status_res.get_json()['review_status'] == 'REVIEWED'

    status_res = client.put(f'/api/incidents/{incident_id}/status', json={'status': 'DISMISSED'})
    assert status_res.status_code == 200
    assert status_res.get_json()['review_status'] == 'DISMISSED'

def test_student_portal_execute_and_submit(client):
    stu_res = client.post('/api/students', json={'name': 'Portal Tester', 'email': 'pt@test.edu', 'register_number': 'PT999'})
    exam_res = client.post('/api/exams', json={'title': 'Portal Exam', 'duration_minutes': 20})
    q_res = client.post(f"/api/exams/{exam_res.get_json()['id']}/questions", json={
        'title': 'Reverse String',
        'description': 'Reverse input string',
        'starter_code': 'def rev(s): return s[::-1]',
        'language': 'python'
    })
    sess_res = client.post('/api/sessions', json={'student_id': stu_res.get_json()['id'], 'exam_id': exam_res.get_json()['id']})
    session_id = sess_res.get_json()['id']
    question_id = q_res.get_json()['id']

    # Test /student/execute
    exec_res = client.post('/student/execute', json={
        'question_id': question_id,
        'code': 'def rev(s): return s[::-1]',
        'language': 'python'
    })
    assert exec_res.status_code == 200
    assert exec_res.get_json()['status'] == 'Accepted'
    assert exec_res.get_json()['score'] == 100

    # Test /student/submit
    sub_res = client.post('/student/submit', json={
        'session_id': session_id,
        'question_id': question_id,
        'code': 'def rev(s): return s[::-1]',
        'language': 'python'
    })
    assert sub_res.status_code == 200
    assert sub_res.get_json()['success'] is True
    assert sub_res.get_json()['score'] == 100

    # Test /student/finish via GET & POST
    finish_res = client.get(f'/student/finish/{session_id}', follow_redirects=True)
    assert finish_res.status_code == 200

    # Test faculty incident status update via JSON PUT & POST
    inc_res = client.post('/api/incidents', json={
        'session_id': session_id,
        'incident_type': 'PHONE_DETECTED',
        'severity': 'HIGH'
    })
    assert inc_res.status_code == 201
    inc_id = inc_res.get_json()['id']

    fac_res = client.post(f'/faculty/incidents/{inc_id}/status', json={'status': 'REVIEWED'})
    assert fac_res.status_code == 200
    assert fac_res.get_json()['incident']['review_status'] == 'REVIEWED'

    fac_res_put = client.put(f'/faculty/incidents/{inc_id}/status', json={'status': 'DISMISSED'})
    assert fac_res_put.status_code == 200
    assert fac_res_put.get_json()['incident']['review_status'] == 'DISMISSED'

    # Test invalid status returns 400
    fac_res_invalid = client.put(f'/faculty/incidents/{inc_id}/status', json={'status': 'INVALID_STATUS'})
    assert fac_res_invalid.status_code == 400
    assert fac_res_invalid.get_json()['success'] is False


def test_faculty_crud_and_dual_mode(client):
    # 1. Test Dashboard Dual Mode
    dash_html = client.get('/faculty/dashboard')
    assert dash_html.status_code == 200
    assert b'Faculty Oversight Dashboard' in dash_html.data

    dash_json = client.get('/faculty/dashboard', headers={'Accept': 'application/json'})
    assert dash_json.status_code == 200
    assert dash_json.get_json()['success'] is True
    assert 'metrics' in dash_json.get_json()

    # 2. Test Exam REST Endpoints on /faculty
    create_exam_res = client.post('/faculty/exams', json={
        'title': 'Faculty Exam 101',
        'description': 'Introductory Course Exam',
        'duration_minutes': 45
    })
    assert create_exam_res.status_code == 201
    f_exam_id = create_exam_res.get_json()['id']

    get_exam_res = client.get(f'/faculty/exams/{f_exam_id}', headers={'Accept': 'application/json'})
    assert get_exam_res.status_code == 200
    assert get_exam_res.get_json()['title'] == 'Faculty Exam 101'

    edit_exam_res = client.put(f'/faculty/exams/{f_exam_id}', json={
        'title': 'Faculty Exam 101 Advanced',
        'duration_minutes': 50
    })
    assert edit_exam_res.status_code == 200
    assert edit_exam_res.get_json()['title'] == 'Faculty Exam 101 Advanced'

    # 3. Test Question Endpoints on /faculty
    add_q_res = client.post(f'/faculty/exams/{f_exam_id}/questions', json={
        'title': 'Factorial Function',
        'description': 'Write recursive factorial',
        'starter_code': 'def fact(n): pass',
        'language': 'python'
    })
    assert add_q_res.status_code == 201
    f_q_id = add_q_res.get_json()['id']

    get_q_res = client.get(f'/faculty/questions/{f_q_id}', headers={'Accept': 'application/json'})
    assert get_q_res.status_code == 200
    assert get_q_res.get_json()['title'] == 'Factorial Function'

    edit_q_res = client.put(f'/faculty/questions/{f_q_id}', json={
        'title': 'Factorial & Memoization'
    })
    assert edit_q_res.status_code == 200
    assert edit_q_res.get_json()['title'] == 'Factorial & Memoization'

    del_q_res = client.delete(f'/faculty/questions/{f_q_id}', headers={'Accept': 'application/json'})
    assert del_q_res.status_code == 200
    assert del_q_res.get_json()['success'] is True

    # 4. Test Student REST Endpoints on /faculty
    create_stu_res = client.post('/faculty/students', json={
        'name': 'Sarah Connor',
        'email': 'sarah@test.edu',
        'register_number': 'FAC_STU_001'
    })
    assert create_stu_res.status_code == 201
    f_stu_id = create_stu_res.get_json()['id']

    get_stu_res = client.get(f'/faculty/students/{f_stu_id}', headers={'Accept': 'application/json'})
    assert get_stu_res.status_code == 200
    assert get_stu_res.get_json()['name'] == 'Sarah Connor'

    del_stu_res = client.delete(f'/faculty/students/{f_stu_id}', headers={'Accept': 'application/json'})
    assert del_stu_res.status_code == 200
    assert del_stu_res.get_json()['success'] is True

    # 5. Delete Exam
    del_exam_res = client.delete(f'/faculty/exams/{f_exam_id}', headers={'Accept': 'application/json'})
    assert del_exam_res.status_code == 200
    assert del_exam_res.get_json()['success'] is True


def test_monitoring_routes_and_direct_flags(client):
    # 1. Monitoring Status & Root Endpoint
    status_res = client.get('/api/monitor/status')
    assert status_res.status_code == 200
    assert status_res.get_json()['status'] == 'OPERATIONAL'

    root_get = client.get('/api/monitor')
    assert root_get.status_code == 200

    # 2. Direct telemetry flags without simulation
    res_3faces_flag = client.post('/api/monitor', json={'three_faces': True})
    assert res_3faces_flag.status_code == 200
    data_3 = res_3faces_flag.get_json()
    assert data_3['face_count'] == 3
    assert data_3['incident_type'] == 'MULTIPLE_FACES'
    assert data_3['severity'] == 'HIGH'

    res_phone_flag = client.post('/api/monitor', json={'phone': True})
    assert res_phone_flag.status_code == 200
    assert res_phone_flag.get_json()['incident_type'] == 'PHONE_DETECTED'
    assert res_phone_flag.get_json()['severity'] == 'HIGH'

    res_gaze_flag = client.post('/api/monitor', json={'gaze': True})
    assert res_gaze_flag.status_code == 200
    assert res_gaze_flag.get_json()['incident_type'] == 'GAZE_SHIFT'
    assert res_gaze_flag.get_json()['severity'] == 'LOW'

    res_app_flag = client.post('/api/monitor', json={'app': True})
    assert res_app_flag.status_code == 200
    assert res_app_flag.get_json()['incident_type'] == 'UNAUTHORIZED_APPLICATION'
    assert res_app_flag.get_json()['severity'] == 'HIGH'

    # 3. Audio endpoint direct flags and simulation
    audio_get = client.get('/api/monitor/audio')
    assert audio_get.status_code == 200

    audio_speech_flag = client.post('/api/monitor/audio', json={'speech': True})
    assert audio_speech_flag.status_code == 200
    assert audio_speech_flag.get_json()['incident_type'] == 'SPEECH_DETECTED'
    assert audio_speech_flag.get_json()['severity'] == 'HIGH'

    audio_mv_flag = client.post('/api/monitor/audio', json={'multi_voice': True})
    assert audio_mv_flag.status_code == 200
    assert audio_mv_flag.get_json()['incident_type'] == 'MULTIPLE_VOICES_DETECTED'
    assert audio_mv_flag.get_json()['severity'] == 'HIGH'



