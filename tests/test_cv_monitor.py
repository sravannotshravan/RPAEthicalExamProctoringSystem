import cv2
import numpy as np
from app.services.cv_monitor import CVMonitorService, get_cv_monitor
from app.models import db, Student, Exam, ExamSession, Incident

def test_cv_service_direct_classification():
    service = get_cv_monitor()

    # 1. Test 0 faces
    res_0 = service._classify_face_count(0)
    assert res_0['status'] == 'INCIDENT'
    assert res_0['incident_type'] == 'NO_FACE'
    assert res_0['severity'] == 'LOW'

    # 2. Test 1 face
    res_1 = service._classify_face_count(1)
    assert res_1['status'] == 'NORMAL'
    assert res_1['incident_type'] is None

    # 3. Test 2 faces -> MEDIUM
    res_2 = service._classify_face_count(2)
    assert res_2['status'] == 'INCIDENT'
    assert res_2['incident_type'] == 'MULTIPLE_FACES'
    assert res_2['severity'] == 'MEDIUM'

    # 4. Test 3+ faces -> HIGH
    res_3 = service._classify_face_count(3)
    assert res_3['status'] == 'INCIDENT'
    assert res_3['incident_type'] == 'MULTIPLE_FACES'
    assert res_3['severity'] == 'HIGH'

def test_cv_service_blank_frame_bytes():
    service = get_cv_monitor()

    # Create a solid gray image (no faces present)
    blank_img = np.zeros((300, 300, 3), dtype=np.uint8)
    success, buffer = cv2.imencode('.jpg', blank_img)
    assert success is True

    result = service.analyze_frame_bytes(buffer.tobytes())
    assert result['success'] is True
    assert result['face_count'] == 0
    assert result['status'] == 'INCIDENT'
    assert result['incident_type'] == 'NO_FACE'

def test_monitor_analyze_endpoint_simulations(client):
    # Setup student, exam, and active session
    stu_res = client.post('/api/students', json={'name': 'Grace', 'email': 'grace@test.edu', 'register_number': 'REG801'})
    exam_res = client.post('/api/exams', json={'title': 'Algorithms Test', 'duration_minutes': 30})
    sess_res = client.post('/api/sessions', json={'student_id': stu_res.get_json()['id'], 'exam_id': exam_res.get_json()['id']})
    session_id = sess_res.get_json()['id']

    # Activate session
    client.post(f'/api/sessions/{session_id}/start')

    # 1. Analyze with simulation = 'no_face'
    res = client.post('/api/monitor/analyze', json={
        'session_id': session_id,
        'simulation': 'no_face'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'INCIDENT'
    assert data['incident_type'] == 'NO_FACE'
    assert data['incident_logged'] is True

    # 2. Check that incident was stored in session
    inc_res = client.get(f'/api/sessions/{session_id}/incidents')
    assert inc_res.status_code == 200
    incidents = inc_res.get_json()
    assert len(incidents) >= 1
    assert incidents[0]['incident_type'] == 'NO_FACE'

    # 3. Analyze with simulation = 'three_faces' -> HIGH severity
    res_3faces = client.post('/api/monitor/analyze', json={
        'session_id': session_id,
        'simulation': 'three_faces'
    })
    assert res_3faces.status_code == 200
    data_3 = res_3faces.get_json()
    assert data_3['incident_type'] == 'MULTIPLE_FACES'
    assert data_3['severity'] == 'HIGH'

    # 4. Analyze with simulation = 'gaze_shift' -> LOW severity
    res_gaze = client.post('/api/monitor/analyze', json={
        'session_id': session_id,
        'simulation': 'gaze_shift'
    })
    assert res_gaze.status_code == 200
    data_gaze = res_gaze.get_json()
    assert data_gaze['incident_type'] == 'GAZE_SHIFT'
    assert data_gaze['severity'] == 'LOW'

    # 5. Analyze with simulation = 'phone_detected' -> HIGH severity
    res_phone = client.post('/api/monitor/analyze', json={
        'session_id': session_id,
        'simulation': 'phone_detected'
    })
    assert res_phone.status_code == 200
    data_phone = res_phone.get_json()
    assert data_phone['incident_type'] == 'PHONE_DETECTED'
    assert data_phone['severity'] == 'HIGH'

    # 6. Analyze with simulation = 'unauthorized_application' -> HIGH severity
    res_app = client.post('/api/monitor/analyze', json={
        'session_id': session_id,
        'simulation': 'unauthorized_application'
    })
    assert res_app.status_code == 200
    data_app = res_app.get_json()
    assert data_app['incident_type'] == 'UNAUTHORIZED_APPLICATION'
    assert data_app['severity'] == 'HIGH'

    # 7. Analyze with simulation = 'prohibited_device' -> HIGH severity
    res_dev = client.post('/api/monitor/analyze', json={
        'session_id': session_id,
        'simulation': 'prohibited_device'
    })
    assert res_dev.status_code == 200
    data_dev = res_dev.get_json()
    assert data_dev['incident_type'] == 'PROHIBITED_DEVICE_DETECTED'
    assert data_dev['severity'] == 'HIGH'

    # 8. Test Audio Monitoring API - Speech Detected
    res_audio_speech = client.post('/api/monitor/audio', json={
        'session_id': session_id,
        'simulation': 'speech'
    })
    assert res_audio_speech.status_code == 200
    data_speech = res_audio_speech.get_json()
    assert data_speech['status'] == 'INCIDENT'
    assert data_speech['incident_type'] == 'SPEECH_DETECTED'
    assert data_speech['severity'] == 'HIGH'
    assert data_speech['incident_logged'] is True

    # 9. Test Audio Monitoring API - Acoustic Noise Spike
    res_audio_noise = client.post('/api/monitor/audio', json={
        'session_id': session_id,
        'simulation': 'noise'
    })
    assert res_audio_noise.status_code == 200
    data_noise = res_audio_noise.get_json()
    assert data_noise['incident_type'] == 'AUDIO_ANOMALY'
    assert data_noise['severity'] == 'MEDIUM'

    # 10. Test Audio Monitoring API - Multiple Voices
    res_multi_voice = client.post('/api/monitor/audio', json={
        'session_id': session_id,
        'simulation': 'multiple_voices'
    })
    assert res_multi_voice.status_code == 200
    data_mv = res_multi_voice.get_json()
    assert data_mv['incident_type'] == 'MULTIPLE_VOICES_DETECTED'
    assert data_mv['severity'] == 'HIGH'

    # 11. Analyze with simulation = 'normal'
    res_normal = client.post('/api/monitor/analyze', json={
        'session_id': session_id,
        'simulation': 'normal'
    })
    assert res_normal.status_code == 200
    assert res_normal.get_json()['success'] is True
    assert res_normal.get_json()['status'] == 'NORMAL'
    assert res_normal.get_json()['incident_logged'] is False

    # 12. Test simulation aliases & string session_id conversion
    res_alias_3 = client.post('/api/monitor/analyze', json={
        'session_id': str(session_id),
        'simulation': '3_faces'
    })
    assert res_alias_3.status_code == 200
    assert res_alias_3.get_json()['success'] is True
    assert res_alias_3.get_json()['severity'] == 'HIGH'

    res_alias_phone = client.post('/api/monitor/analyze', json={
        'session_id': str(session_id),
        'simulation': 'phone'
    })
    assert res_alias_phone.status_code == 200
    assert res_alias_phone.get_json()['incident_type'] == 'PHONE_DETECTED'
    assert res_alias_phone.get_json()['severity'] == 'HIGH'

