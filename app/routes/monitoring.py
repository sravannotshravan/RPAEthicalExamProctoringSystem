from datetime import datetime, timezone
import logging
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, ExamSession, Incident
from app.services.cv_monitor import get_cv_monitor
from app.services.audio_monitor import get_audio_monitor

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint('monitoring', __name__)

DEBOUNCE_SECONDS = 5
VALID_SEVERITIES = {'LOW', 'MEDIUM', 'HIGH'}
_FALSY_STRINGS = {'', '0', 'false', 'no', 'off', 'none', 'null'}


def _request_payload():
    """Returns the request body as a dict (JSON object or form), never a list/scalar."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = request.form.to_dict() or {}
    return data


def _as_bool(value):
    """Interprets JSON booleans and form strings ('false', '0', ...) correctly."""
    if isinstance(value, str):
        return value.strip().lower() not in _FALSY_STRINGS
    return bool(value)


def _as_int(value, default=None):
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _as_float(value, default):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _normalize_severity(value, default):
    severity = str(value).strip().upper() if value is not None else ''
    return severity if severity in VALID_SEVERITIES else default


def _log_incident(session_id, incident_type, severity, source, details, bypass_debounce):
    """
    Persists an incident for an active session, debouncing repeats of the same type
    within DEBOUNCE_SECONDS. Returns (incident_logged, incident_id).
    """
    try:
        session = db.session.get(ExamSession, session_id)
        if not session or session.status == 'COMPLETED':
            return False, None

        recent_incident = Incident.query.filter(
            Incident.session_id == session_id,
            Incident.incident_type == incident_type
        ).order_by(Incident.id.desc()).first()

        if not bypass_debounce and recent_incident and recent_incident.timestamp:
            inc_ts = recent_incident.timestamp
            if inc_ts.tzinfo is None:
                inc_ts = inc_ts.replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - inc_ts).total_seconds() < DEBOUNCE_SECONDS:
                return False, recent_incident.id

        incident = Incident(
            session_id=session_id,
            incident_type=incident_type,
            severity=severity,
            source=source,
            details=details,
            review_status='PENDING',
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(incident)
        db.session.commit()
        return True, incident.id
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.warning("Error logging %s incident for session %s: %s", source, session_id, e)
        return False, None


@monitoring_bp.route('/status', methods=['GET'])
def monitoring_status():
    """Returns general health and operational capabilities of the monitoring subsystem."""
    return jsonify({
        'success': True,
        'status': 'OPERATIONAL',
        'subsystems': {
            'visual_cv': 'Active (Haar Cascades, Multi-Face, Gaze, Device Detection)',
            'acoustic_proctoring': 'Active (Web Audio API, RMS Energy, Voice Activity)'
        },
        'endpoints': {
            'analyze_visual': '/api/monitor/analyze',
            'analyze_audio': '/api/monitor/audio',
            'status': '/api/monitor/status'
        },
        'supported_simulations': [
            'normal', 'no_face', 'multiple_faces', 'three_faces',
            'gaze_shift', 'phone_detected', 'prohibited_device',
            'unauthorized_application', 'speech_detected', 'audio_detected',
            'multiple_voices'
        ]
    }), 200


@monitoring_bp.route('', methods=['GET', 'POST'])
@monitoring_bp.route('/', methods=['GET', 'POST'])
@monitoring_bp.route('/analyze', methods=['GET', 'POST'])
def analyze_frame():
    """
    Analyzes visual & environment telemetry for anomalies:
    - 0 faces: NO_FACE (Low)
    - 2 faces: MULTIPLE_FACES (Medium)
    - 3+ faces: MULTIPLE_FACES (High)
    - Gaze / head shift: GAZE_SHIFT (Low)
    - Mobile phone in frame: PHONE_DETECTED (High)
    - Prohibited device in frame: PROHIBITED_DEVICE_DETECTED (High)
    - Unauthorized desktop app: UNAUTHORIZED_APPLICATION (High)
    - Audio speech/anomaly: SPEECH_DETECTED / AUDIO_ANOMALY (High/Medium)
    """
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'endpoint': '/api/monitor/analyze',
            'status': 'READY',
            'message': 'Send a POST request with webcam image base64, simulation key, or telemetry metrics.'
        }), 200

    data = _request_payload()
    session_id = _as_int(data.get('session_id'))
    image_b64 = data.get('image') or data.get('image_b64') or data.get('frame')
    simulation = data.get('simulation') or data.get('sim') or data.get('mode')

    def flag(*keys):
        return any(_as_bool(data.get(k)) for k in keys)

    bypass_debounce = flag('force', 'bypass_debounce', 'ignore_debounce')

    # 1. Simulation mode (for demonstration and manual testing)
    if simulation:
        sim_raw = str(simulation).lower().strip()
        sim_key = sim_raw.replace('-', '_').replace(' ', '_')
        sim_map = {
            'no_face': {
                'face_count': 0,
                'status': 'INCIDENT',
                'incident_type': 'NO_FACE',
                'severity': 'LOW',
                'source': 'CV',
                'details': 'No face detected in webcam view. Candidate may have moved out of frame.'
            },
            'multiple_faces': {
                'face_count': 2,
                'status': 'INCIDENT',
                'incident_type': 'MULTIPLE_FACES',
                'severity': 'MEDIUM',
                'source': 'CV',
                'details': 'Multiple faces (2) detected in webcam frame. Additional person may be present.'
            },
            'three_faces': {
                'face_count': 3,
                'status': 'INCIDENT',
                'incident_type': 'MULTIPLE_FACES',
                'severity': 'HIGH',
                'source': 'CV',
                'details': 'Critical visual anomaly: 3 faces detected in webcam frame. Multiple unauthorized individuals present.'
            },
            'gaze_shift': {
                'face_count': 1,
                'status': 'INCIDENT',
                'incident_type': 'GAZE_SHIFT',
                'severity': 'LOW',
                'source': 'CV',
                'details': 'Candidate head orientation or gaze shifted away from exam screen for >3 seconds.'
            },
            'phone_detected': {
                'face_count': 1,
                'status': 'INCIDENT',
                'incident_type': 'PHONE_DETECTED',
                'severity': 'HIGH',
                'source': 'CV',
                'details': 'Mobile phone or handheld electronic device detected in candidate webcam frame.'
            },
            'prohibited_device': {
                'face_count': 1,
                'status': 'INCIDENT',
                'incident_type': 'PROHIBITED_DEVICE_DETECTED',
                'severity': 'HIGH',
                'source': 'CV',
                'details': 'Prohibited external device (smartwatch, secondary display, or earphones) observed in frame.'
            },
            'unauthorized_application': {
                'face_count': 1,
                'status': 'INCIDENT',
                'incident_type': 'UNAUTHORIZED_APPLICATION',
                'severity': 'HIGH',
                'source': 'BROWSER_INTEGRITY',
                'details': data.get('details') or 'Unauthorized application or window blur detected. Candidate switched away from active exam.'
            },
            'speech_detected': {
                'face_count': 1,
                'status': 'INCIDENT',
                'incident_type': 'SPEECH_DETECTED',
                'severity': 'HIGH',
                'source': 'AUDIO',
                'details': 'Conversational voice/speech detected in candidate environment. Potential verbal communication.'
            },
            'audio_detected': {
                'face_count': 1,
                'status': 'INCIDENT',
                'incident_type': 'AUDIO_ANOMALY',
                'severity': 'MEDIUM',
                'source': 'AUDIO',
                'details': 'Acoustic spike or sustained ambient noise detected exceeding proctoring threshold.'
            },
            'multiple_voices': {
                'face_count': 1,
                'status': 'INCIDENT',
                'incident_type': 'MULTIPLE_VOICES_DETECTED',
                'severity': 'HIGH',
                'source': 'AUDIO',
                'details': 'Secondary or multiple distinct voices detected in exam room audio stream.'
            },
            'normal': {
                'face_count': 1,
                'status': 'NORMAL',
                'incident_type': None,
                'severity': None,
                'source': 'CV',
                'details': 'Single face verified and centered.'
            }
        }
        # Convenient aliases
        sim_map['0_faces'] = sim_map['0faces'] = sim_map['zero_faces'] = sim_map['noface'] = sim_map['no_face']
        sim_map['2_faces'] = sim_map['2faces'] = sim_map['two_faces'] = sim_map['twofaces'] = sim_map['multiple_faces']
        sim_map['3_faces'] = sim_map['3faces'] = sim_map['threefaces'] = sim_map['three_faces']
        sim_map['gaze'] = sim_map['looking_away'] = sim_map['eye_shift'] = sim_map['gaze_shift']
        sim_map['phone'] = sim_map['mobile_phone'] = sim_map['cellphone'] = sim_map['smartphone'] = sim_map['phone_detected']
        sim_map['device'] = sim_map['smartwatch'] = sim_map['earphones'] = sim_map['headphones'] = sim_map['prohibited_device_detected'] = sim_map['prohibited_device']
        sim_map['app'] = sim_map['window_blur'] = sim_map['tab_switch'] = sim_map['prohibited_process'] = sim_map['unauthorized_application']
        sim_map['speech'] = sim_map['voice'] = sim_map['talking'] = sim_map['conversation'] = sim_map['speech_detected']
        sim_map['noise'] = sim_map['audio'] = sim_map['audio_anomaly'] = sim_map['acoustic_spike'] = sim_map['loud_noise'] = sim_map['audio_detected']
        sim_map['multi_voice'] = sim_map['secondary_voice'] = sim_map['multiple_voices']
        sim_map['clear'] = sim_map['ok'] = sim_map['normal']

        res = sim_map.get(sim_key, sim_map['normal'])
        analysis_result = {
            'success': True,
            **res
        }

    # 2. Direct telemetry flags
    elif flag('three_faces', '3_faces'):
        analysis_result = {
            'success': True,
            'face_count': 3,
            'status': 'INCIDENT',
            'incident_type': 'MULTIPLE_FACES',
            'severity': 'HIGH',
            'source': 'CV',
            'details': data.get('details') or 'Critical visual anomaly: 3 faces detected in webcam frame.'
        }
    elif flag('multiple_faces', '2_faces'):
        analysis_result = {
            'success': True,
            'face_count': 2,
            'status': 'INCIDENT',
            'incident_type': 'MULTIPLE_FACES',
            'severity': 'MEDIUM',
            'source': 'CV',
            'details': data.get('details') or 'Multiple faces (2) detected in webcam frame.'
        }
    elif flag('no_face', 'zero_faces'):
        analysis_result = {
            'success': True,
            'face_count': 0,
            'status': 'INCIDENT',
            'incident_type': 'NO_FACE',
            'severity': 'LOW',
            'source': 'CV',
            'details': data.get('details') or 'No face detected in webcam view.'
        }
    elif flag('phone_detected', 'phone'):
        analysis_result = {
            'success': True,
            'face_count': 1,
            'status': 'INCIDENT',
            'incident_type': 'PHONE_DETECTED',
            'severity': 'HIGH',
            'source': 'CV',
            'details': data.get('details') or 'Mobile phone detected in frame.'
        }
    elif flag('prohibited_device', 'device'):
        analysis_result = {
            'success': True,
            'face_count': 1,
            'status': 'INCIDENT',
            'incident_type': 'PROHIBITED_DEVICE_DETECTED',
            'severity': 'HIGH',
            'source': 'CV',
            'details': data.get('details') or 'Prohibited device detected in frame.'
        }
    elif flag('unauthorized_application', 'app'):
        analysis_result = {
            'success': True,
            'face_count': 1,
            'status': 'INCIDENT',
            'incident_type': 'UNAUTHORIZED_APPLICATION',
            'severity': 'HIGH',
            'source': 'BROWSER_INTEGRITY',
            'details': data.get('details') or 'Unauthorized application or window blur detected.'
        }
    elif flag('gaze_shift', 'gaze'):
        analysis_result = {
            'success': True,
            'face_count': 1,
            'status': 'INCIDENT',
            'incident_type': 'GAZE_SHIFT',
            'severity': 'LOW',
            'source': 'CV',
            'details': data.get('details') or 'Candidate head orientation or gaze shifted away from exam screen.'
        }
    elif flag('speech_detected', 'speech'):
        analysis_result = {
            'success': True,
            'face_count': 1,
            'status': 'INCIDENT',
            'incident_type': 'SPEECH_DETECTED',
            'severity': 'HIGH',
            'source': 'AUDIO',
            'details': data.get('details') or 'Speech detected in proctoring environment.'
        }
    elif flag('multiple_voices', 'multi_voice'):
        analysis_result = {
            'success': True,
            'face_count': 1,
            'status': 'INCIDENT',
            'incident_type': 'MULTIPLE_VOICES_DETECTED',
            'severity': 'HIGH',
            'source': 'AUDIO',
            'details': data.get('details') or 'Multiple distinct voices detected in environment.'
        }
    elif data.get('incident_type'):
        analysis_result = {
            'success': True,
            'face_count': _as_int(data.get('face_count'), 1),
            'status': data.get('status', 'INCIDENT'),
            'incident_type': data.get('incident_type'),
            'severity': _normalize_severity(data.get('severity'), 'HIGH'),
            'source': data.get('source', 'CV'),
            'details': data.get('details') or 'Incident reported via monitoring API.'
        }
    elif 'face_count' in data or 'faces' in data or 'num_faces' in data:
        fc_val = data.get('face_count') if 'face_count' in data else (data.get('faces') if 'faces' in data else data.get('num_faces'))
        fc = _as_int(fc_val)
        if fc is not None and fc >= 0:
            res = get_cv_monitor().classify_face_count(fc)
            analysis_result = {
                'success': True,
                **res,
                'source': 'CV'
            }
        else:
            analysis_result = {
                'success': True,
                'face_count': 1,
                'status': 'NORMAL',
                'incident_type': None,
                'severity': None,
                'source': 'CV',
                'details': 'Single face verified and centered.'
            }

    # 3. Real webcam frame analysis
    elif image_b64:
        try:
            analysis_result = get_cv_monitor().analyze_frame_base64(str(image_b64))
        except FileNotFoundError as e:
            logger.error("CV monitor unavailable: %s", e)
            return jsonify({'success': False, 'status': 'ERROR', 'error': 'CV monitoring service unavailable'}), 503
        analysis_result['source'] = 'CV'

    # 4. Heartbeat ping or missing parameter handling
    else:
        if session_id:
            analysis_result = {
                'success': True,
                'face_count': 1,
                'status': 'NORMAL',
                'incident_type': None,
                'severity': None,
                'source': 'CV',
                'details': 'Heartbeat proctoring ping recorded.'
            }
        else:
            return jsonify({
                'success': False,
                'error': 'Either image, simulation, face_count, or incident_type is required'
            }), 400

    incident_logged = False
    incident_id = None

    # If an incident was detected and session_id is provided, log to DB
    if analysis_result.get('status') == 'INCIDENT' and session_id:
        incident_logged, incident_id = _log_incident(
            session_id,
            analysis_result.get('incident_type') or 'VISUAL_ANOMALY',
            _normalize_severity(analysis_result.get('severity'), 'LOW'),
            analysis_result.get('source') or 'CV',
            analysis_result.get('details', '') or analysis_result.get('error', ''),
            bypass_debounce
        )

    response_payload = {
        'success': bool(analysis_result.get('success', True)),
        'face_count': analysis_result.get('face_count', 0),
        'status': analysis_result.get('status', 'NORMAL'),
        'incident_type': analysis_result.get('incident_type'),
        'severity': analysis_result.get('severity'),
        'source': analysis_result.get('source', 'CV'),
        'details': analysis_result.get('details') or analysis_result.get('error') or '',
        'incident_logged': incident_logged,
        'incident_id': incident_id
    }
    return jsonify(response_payload), 200


@monitoring_bp.route('/audio', methods=['GET', 'POST'])
@monitoring_bp.route('/audio/analyze', methods=['GET', 'POST'])
def analyze_audio():
    """
    Dedicated endpoint for real-time acoustic proctoring telemetry.
    Accepts browser Web Audio volume/dB metrics or audio chunks,
    detects voice/speech, acoustic anomalies, or multiple voices,
    and logs incidents without storing raw audio.
    """
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'endpoint': '/api/monitor/audio',
            'status': 'READY',
            'message': 'Send a POST request with audio volume/dB metrics or simulation key.'
        }), 200

    data = _request_payload()

    def flag(*keys):
        return any(_as_bool(data.get(k)) for k in keys)

    session_id = _as_int(data.get('session_id'))
    volume = _as_float(data.get('volume'), 0.0)
    db_level = _as_float(data.get('db_level'), -60.0)
    speech_detected = flag('speech_detected', 'speech')
    continuous_count = _as_int(data.get('continuous_count'), 1)
    audio_b64 = data.get('audio') or data.get('audio_b64')
    simulation = data.get('simulation') or data.get('sim') or data.get('mode')
    bypass_debounce = flag('force', 'bypass_debounce', 'ignore_debounce')

    audio_svc = get_audio_monitor()

    if simulation:
        sim_norm = str(simulation).lower().replace('-', '_').replace(' ', '_').strip()
        if sim_norm in ['speech', 'speech_detected', 'voice', 'talking', 'conversation']:
            result = audio_svc.analyze_audio_metrics(volume=0.75, speech_detected=True, db_level=-15.0, continuous_count=2)
        elif sim_norm in ['noise', 'audio_detected', 'audio', 'audio_anomaly', 'loud_noise', 'acoustic_spike', 'whisper', 'ambient']:
            result = audio_svc.analyze_audio_metrics(volume=0.55, speech_detected=False, db_level=-25.0, continuous_count=1)
        elif sim_norm in ['multiple_voices', 'multi_voice', 'multiple_voice', 'voices', 'two_voices', 'secondary_voice']:
            result = {
                "success": True,
                "status": "INCIDENT",
                "incident_type": "MULTIPLE_VOICES_DETECTED",
                "severity": "HIGH",
                "volume": 0.8,
                "db_level": -12.0,
                "details": "Secondary or multiple distinct voices detected in exam room audio stream."
            }
        else:
            result = audio_svc.analyze_audio_metrics(volume=0.05, speech_detected=False, db_level=-50.0)
    elif flag('multiple_voices', 'multi_voice'):
        result = {
            "success": True,
            "status": "INCIDENT",
            "incident_type": "MULTIPLE_VOICES_DETECTED",
            "severity": "HIGH",
            "volume": max(0.75, volume),
            "db_level": max(-14.0, db_level),
            "details": data.get('details') or "Secondary or multiple distinct voices detected in exam room audio stream."
        }
    elif data.get('incident_type'):
        result = {
            "success": True,
            "status": data.get('status', 'INCIDENT'),
            "incident_type": data.get('incident_type'),
            "severity": _normalize_severity(data.get('severity'), 'HIGH'),
            "volume": volume,
            "db_level": db_level,
            "details": data.get('details') or f"Audio incident reported: {data.get('incident_type')}"
        }
    elif audio_b64:
        result = audio_svc.analyze_audio_base64(str(audio_b64))
    else:
        result = audio_svc.analyze_audio_metrics(
            volume=volume,
            speech_detected=speech_detected,
            db_level=db_level,
            continuous_count=continuous_count
        )

    incident_logged = False
    incident_id = None

    if result.get('status') == 'INCIDENT' and session_id:
        incident_logged, incident_id = _log_incident(
            session_id,
            result.get('incident_type') or 'AUDIO_ANOMALY',
            _normalize_severity(result.get('severity'), 'MEDIUM'),
            'AUDIO',
            result.get('details', ''),
            bypass_debounce
        )

    return jsonify({
        'success': bool(result.get('success', True)),
        'status': result.get('status', 'NORMAL'),
        'incident_type': result.get('incident_type'),
        'severity': result.get('severity'),
        'source': 'AUDIO',
        'face_count': 1,
        'volume': _as_float(result.get('volume'), 0.0),
        'db_level': _as_float(result.get('db_level'), -60.0),
        'details': result.get('details') or '',
        'incident_logged': incident_logged,
        'incident_id': incident_id
    }), 200
