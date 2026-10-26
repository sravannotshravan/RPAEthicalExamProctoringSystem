from datetime import datetime, timezone
from functools import wraps
import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory, Response
from app.models import db, Student, Exam, Question, ExamSession, Submission, Incident, EnvironmentCheck, AutomationRun
from app.services.excel_report import build_exam_workbook
from app.services.code_runner import execute_mock_code

api_bp = Blueprint('api', __name__)

def require_api_key(f):
    """
    Validates X-API-Key or Bearer token for automated service requests from UiPath.
    If UIPATH_API_KEY is configured, requests must supply a matching key.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        expected_key = current_app.config.get('UIPATH_API_KEY')
        if expected_key:
            auth_header = request.headers.get('Authorization', '')
            api_key = request.headers.get('X-API-Key', '')
            if not api_key and auth_header.startswith('Bearer '):
                api_key = auth_header[7:].strip()
            
            if api_key != expected_key:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Valid X-API-Key or Bearer token required for UiPath service integration.'
                }), 401
        return f(*args, **kwargs)
    return decorated


# ----------------- EXAMS -----------------

@api_bp.route('/exams', methods=['GET'])
def get_exams():
    exams = Exam.query.order_by(Exam.created_at.desc()).all()
    return jsonify([e.to_dict() for e in exams]), 200

@api_bp.route('/exams', methods=['POST'])
def create_exam():
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Exam title is required'}), 400

    exam = Exam(
        title=title,
        description=data.get('description', ''),
        duration_minutes=int(data.get('duration_minutes', 30))
    )
    db.session.add(exam)
    db.session.commit()
    return jsonify(exam.to_dict()), 201

@api_bp.route('/exams/<int:exam_id>', methods=['GET'])
def get_exam(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    exam_data = exam.to_dict()
    exam_data['questions'] = [q.to_dict() for q in exam.questions]
    return jsonify(exam_data), 200

@api_bp.route('/exams/<int:exam_id>', methods=['PUT'])
def update_exam(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    data = request.get_json() or {}
    if 'title' in data and data['title'].strip():
        exam.title = data['title'].strip()
    if 'description' in data:
        exam.description = data['description']
    if 'duration_minutes' in data:
        exam.duration_minutes = int(data['duration_minutes'])
    db.session.commit()
    return jsonify(exam.to_dict()), 200

@api_bp.route('/exams/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    db.session.delete(exam)
    db.session.commit()
    return jsonify({'message': 'Exam deleted successfully', 'id': exam_id}), 200

# ----------------- QUESTIONS -----------------

@api_bp.route('/exams/<int:exam_id>/questions', methods=['GET'])
def get_questions_for_exam(exam_id):
    db.get_or_404(Exam, exam_id)
    questions = Question.query.filter_by(exam_id=exam_id).all()
    return jsonify([q.to_dict() for q in questions]), 200

@api_bp.route('/exams/<int:exam_id>/questions', methods=['POST'])
def add_question(exam_id):
    db.get_or_404(Exam, exam_id)
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    if not title or not description:
        return jsonify({'error': 'Title and description are required'}), 400

    question = Question(
        exam_id=exam_id,
        title=title,
        description=description,
        starter_code=data.get('starter_code', '# Write your code here\n'),
        language=data.get('language', 'python')
    )
    db.session.add(question)
    db.session.commit()
    return jsonify(question.to_dict()), 201

@api_bp.route('/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    question = db.get_or_404(Question, question_id)
    return jsonify(question.to_dict()), 200

@api_bp.route('/questions/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    question = db.get_or_404(Question, question_id)
    data = request.get_json() or {}
    if 'title' in data and data['title'].strip():
        question.title = data['title'].strip()
    if 'description' in data and data['description'].strip():
        question.description = data['description'].strip()
    if 'starter_code' in data:
        question.starter_code = data['starter_code']
    if 'language' in data:
        question.language = data['language']
    db.session.commit()
    return jsonify(question.to_dict()), 200

@api_bp.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    question = db.get_or_404(Question, question_id)
    exam_id = question.exam_id
    db.session.delete(question)
    db.session.commit()
    return jsonify({'message': 'Question deleted successfully', 'id': question_id, 'exam_id': exam_id}), 200

# ----------------- STUDENTS -----------------

@api_bp.route('/students', methods=['GET'])
def get_students():
    students = Student.query.order_by(Student.name.asc()).all()
    return jsonify([s.to_dict() for s in students]), 200

@api_bp.route('/students', methods=['POST'])
def create_student():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    register_number = data.get('register_number', '').strip()

    if not name or not email or not register_number:
        return jsonify({'error': 'Name, email, and register_number are required'}), 400

    if Student.query.filter((Student.email == email) | (Student.register_number == register_number)).first():
        return jsonify({'error': 'Student with given email or register number already exists'}), 409

    student = Student(name=name, email=email, register_number=register_number)
    db.session.add(student)
    db.session.commit()
    return jsonify(student.to_dict()), 201

@api_bp.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    student = db.get_or_404(Student, student_id)
    return jsonify(student.to_dict()), 200

@api_bp.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    student = db.get_or_404(Student, student_id)
    data = request.get_json() or {}
    if 'name' in data and data['name'].strip():
        student.name = data['name'].strip()
    if 'email' in data and data['email'].strip():
        student.email = data['email'].strip()
    if 'register_number' in data and data['register_number'].strip():
        student.register_number = data['register_number'].strip()
    db.session.commit()
    return jsonify(student.to_dict()), 200

@api_bp.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    student = db.get_or_404(Student, student_id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({'message': 'Student deleted successfully', 'id': student_id}), 200

# ----------------- SESSIONS -----------------

@api_bp.route('/sessions', methods=['GET'])
def get_sessions():
    sessions = ExamSession.query.order_by(ExamSession.id.desc()).all()
    return jsonify([s.to_dict() for s in sessions]), 200

@api_bp.route('/sessions', methods=['POST'])
def create_session():
    data = request.get_json() or {}
    exam_id = data.get('exam_id')
    student_id = data.get('student_id')

    if not exam_id or not student_id:
        return jsonify({'error': 'exam_id and student_id are required'}), 400

    db.get_or_404(Exam, exam_id)
    db.get_or_404(Student, student_id)

    # Check if an active or not_started session already exists for this exam/student
    existing = ExamSession.query.filter_by(
        exam_id=exam_id,
        student_id=student_id,
        status='ACTIVE'
    ).first()
    if existing:
        return jsonify(existing.to_dict()), 200

    session = ExamSession(
        exam_id=exam_id,
        student_id=student_id,
        status='NOT_STARTED'
    )
    db.session.add(session)
    db.session.commit()
    return jsonify(session.to_dict()), 201

@api_bp.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    session = db.get_or_404(ExamSession, session_id)
    data = session.to_dict()
    data['exam_description'] = session.exam.description if session.exam else ''
    data['duration_minutes'] = session.exam.duration_minutes if session.exam else 30
    data['questions'] = [q.to_dict() for q in session.exam.questions] if session.exam else []
    data['submissions'] = [sub.to_dict() for sub in session.submissions]
    data['incidents'] = [inc.to_dict() for inc in session.incidents]
    return jsonify(data), 200

@api_bp.route('/sessions/<int:session_id>/start', methods=['POST'])
def start_session(session_id):
    session = db.get_or_404(ExamSession, session_id)
    now = datetime.now(timezone.utc)
    session.started_at = now
    session.status = 'ACTIVE'
    session.consent_given = True
    session.consent_timestamp = now
    db.session.commit()
    return jsonify(session.to_dict()), 200

@api_bp.route('/sessions/<int:session_id>/finish', methods=['POST'])
def finish_session(session_id):
    session = db.get_or_404(ExamSession, session_id)
    session.ended_at = datetime.now(timezone.utc)
    session.status = 'COMPLETED'
    db.session.commit()
    return jsonify(session.to_dict()), 200

# ----------------- CODE EXECUTION & SUBMISSIONS -----------------

@api_bp.route('/code/run', methods=['POST'])
def run_code():
    data = request.get_json() or {}
    code = data.get('code', '')
    language = data.get('language', 'python')
    question_id = data.get('question_id')
    result = execute_mock_code(code=code, language=language, question_id=question_id)
    return jsonify(result), 200

@api_bp.route('/submissions', methods=['POST'])
def create_submission():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    question_id = data.get('question_id')
    code = data.get('code', '')
    language = data.get('language', 'python')

    if not session_id or not question_id:
        return jsonify({'error': 'session_id and question_id are required'}), 400

    session = db.get_or_404(ExamSession, session_id)
    db.get_or_404(Question, question_id)

    # Run mock execution service
    exec_result = execute_mock_code(code=code, language=language, question_id=question_id)

    # Check if a submission for this session and question already exists; update or create
    submission = Submission.query.filter_by(session_id=session_id, question_id=question_id).first()
    if submission:
        submission.code = code
        submission.language = language
        submission.output = exec_result.get('output', '')
        submission.score = exec_result.get('score', 100)
        submission.submitted_at = datetime.now(timezone.utc)
    else:
        submission = Submission(
            session_id=session_id,
            question_id=question_id,
            code=code,
            language=language,
            output=exec_result.get('output', ''),
            score=exec_result.get('score', 100),
            submitted_at=datetime.now(timezone.utc)
        )
        db.session.add(submission)

    db.session.commit()
    res = submission.to_dict()
    res['mock_result'] = exec_result
    return jsonify(res), 201

# ----------------- INCIDENTS -----------------

@api_bp.route('/sessions/<int:session_id>/incidents', methods=['GET'])
def get_session_incidents(session_id):
    db.get_or_404(ExamSession, session_id)
    incidents = Incident.query.filter_by(session_id=session_id).order_by(Incident.timestamp.desc()).all()
    return jsonify([i.to_dict() for i in incidents]), 200

@api_bp.route('/incidents', methods=['POST'])
def create_incident():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    incident_type = data.get('incident_type')

    if not session_id or not incident_type:
        return jsonify({'error': 'session_id and incident_type are required'}), 400

    db.get_or_404(ExamSession, session_id)

    incident = Incident(
        session_id=session_id,
        incident_type=incident_type,
        severity=data.get('severity', 'LOW'),
        source=data.get('source', 'CV'),
        details=data.get('details', ''),
        review_status='PENDING',
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(incident)
    db.session.commit()
    return jsonify(incident.to_dict()), 201

@api_bp.route('/incidents/<int:incident_id>/status', methods=['PUT'])
def update_incident_status(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    data = request.get_json() or {}
    status = data.get('status', '').upper()

    if status not in ['PENDING', 'REVIEWED', 'DISMISSED']:
        return jsonify({'error': 'Invalid review status. Allowed: PENDING, REVIEWED, DISMISSED'}), 400

    incident.review_status = status
    db.session.commit()
    return jsonify(incident.to_dict()), 200

# ----------------- UIPATH INTEGRATION & AUTOMATION -----------------

@api_bp.route('/health', methods=['GET'])
def health_check():
    """System health check and UiPath integration diagnostic status."""
    project_dir = current_app.config.get('UIPATH_PROJECT_DIR', '')
    uipath_ready = os.path.isdir(project_dir) and os.path.isfile(os.path.join(project_dir, 'project.json'))
    
    # Check pending runs
    pending_runs = AutomationRun.query.filter_by(status='PENDING').count()
    active_runs = AutomationRun.query.filter_by(status='RUNNING').count()

    return jsonify({
        'status': 'HEALTHY',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'database': 'CONNECTED',
        'uipath_project_available': uipath_ready,
        'uipath_project_path': project_dir,
        'pending_automation_runs': pending_runs,
        'active_automation_runs': active_runs
    }), 200


@api_bp.route('/sessions/eligible', methods=['GET'])
def get_eligible_session():
    """
    Returns an eligible exam session for attended/unattended automation execution.
    Prioritizes active sessions or sessions in NOT_STARTED state.
    """
    exam_id = request.args.get('exam_id', type=int)
    query = ExamSession.query
    if exam_id:
        query = query.filter_by(exam_id=exam_id)

    # Prefer active session, then not_started
    session = query.filter_by(status='ACTIVE').order_by(ExamSession.id.desc()).first()
    if not session:
        session = query.filter_by(status='NOT_STARTED').order_by(ExamSession.id.desc()).first()

    if not session:
        return jsonify({'message': 'No eligible session found', 'session': None}), 404

    return jsonify({'session': session.to_dict()}), 200


@api_bp.route('/sessions/<int:session_id>/environment-check', methods=['POST'])
@require_api_key
def submit_environment_check(session_id):
    """
    Receives environment verification results from the UiPath EnvironmentVerification workflow.
    Validates payload and records the check. If prohibited processes or hardware failures are observed,
    logs an incident as an observation without drawing conclusions about student intent.
    """
    session = db.get_or_404(ExamSession, session_id)
    data = request.get_json() or {}

    status = data.get('status', 'PASSED').upper()
    if status not in ['PASSED', 'FLAGGED', 'FAILED', 'UNKNOWN']:
        status = 'FLAGGED'

    internet_status = data.get('internet_status', 'OK')
    browser_detected = data.get('browser_detected', '')
    webcam_status = data.get('webcam_status', 'AVAILABLE')
    microphone_status = data.get('microphone_status', 'AVAILABLE')
    prohibited_processes = data.get('prohibited_processes', '')
    if isinstance(prohibited_processes, list):
        prohibited_processes = ', '.join(str(p) for p in prohibited_processes)
    summary = data.get('summary', 'Automated UiPath environment verification completed.')

    # Idempotency check: if an identical check for this session was submitted recently, return existing
    last_check = EnvironmentCheck.query.filter_by(session_id=session_id).order_by(EnvironmentCheck.id.desc()).first()
    if last_check and last_check.status == status and last_check.prohibited_processes == prohibited_processes:
        # Check if within recent window (30 seconds)
        now_utc = datetime.now(timezone.utc)
        check_time = last_check.checked_at.replace(tzinfo=timezone.utc) if last_check.checked_at.tzinfo is None else last_check.checked_at
        if (now_utc - check_time).total_seconds() < 30:
            return jsonify({
                'message': 'Environment check already recorded (idempotent)',
                'environment_check': last_check.to_dict()
            }), 200

    check = EnvironmentCheck(
        session_id=session_id,
        status=status,
        internet_status=internet_status,
        browser_detected=browser_detected,
        webcam_status=webcam_status,
        microphone_status=microphone_status,
        prohibited_processes=prohibited_processes,
        summary=summary,
        checked_at=datetime.now(timezone.utc)
    )
    db.session.add(check)

    # If flagged or failed, log an objective observation incident
    if status in ['FLAGGED', 'FAILED'] or prohibited_processes:
        if prohibited_processes:
            incident_type = 'PROHIBITED_PROCESS_DETECTED'
            severity = 'HIGH'
            details = f"Observation: Potentially conflicting or prohibited process(es) observed running: {prohibited_processes}. Requires human proctor verification."
        else:
            incident_type = 'ENVIRONMENT_CHECK_FAILED'
            severity = 'MEDIUM' if status == 'FLAGGED' else 'HIGH'
            details = f"Observation: Environment check reported {status}. Details: {summary}. Requires human proctor verification."

        # Debounce check for incident
        existing_inc = Incident.query.filter_by(
            session_id=session_id,
            incident_type=incident_type,
            source='UiPath',
            details=details
        ).first()
        if not existing_inc:
            inc = Incident(
                session_id=session_id,
                incident_type=incident_type,
                severity=severity,
                source='UiPath',
                details=details,
                review_status='PENDING',
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(inc)

    db.session.commit()
    return jsonify({
        'message': 'Environment check recorded successfully',
        'environment_check': check.to_dict()
    }), 201


@api_bp.route('/sessions/<int:session_id>/environment-check', methods=['GET'])
def get_environment_check(session_id):
    """Retrieves the latest environment verification results for a session."""
    session = db.get_or_404(ExamSession, session_id)
    latest = session.environment_checks[0] if session.environment_checks else None
    if not latest:
        return jsonify({'message': 'No environment check recorded for this session', 'environment_check': None}), 404
    return jsonify({'environment_check': latest.to_dict()}), 200


@api_bp.route('/incidents/pending', methods=['GET'])
@require_api_key
def get_pending_incidents():
    """Returns all pending incidents across all sessions for IncidentProcessing workflow."""
    exam_id = request.args.get('exam_id', type=int)
    session_id = request.args.get('session_id', type=int)

    query = Incident.query.filter_by(review_status='PENDING')
    if session_id:
        query = query.filter_by(session_id=session_id)
    elif exam_id:
        query = query.join(ExamSession).filter(ExamSession.exam_id == exam_id)

    incidents = query.order_by(Incident.timestamp.desc()).all()
    return jsonify([i.to_dict() for i in incidents]), 200


@api_bp.route('/exams/<int:exam_id>/report-data', methods=['GET'])
@require_api_key
def get_exam_report_data(exam_id):
    """
    Returns complete structured data required by GenerateExamReport.xaml.
    Includes exam details, sessions, student profiles, environment check summaries,
    incident logs, and submissions with scores. Sensitive authentication data is excluded.
    """
    exam = db.get_or_404(Exam, exam_id)
    sessions = exam.sessions

    total_sessions = len(sessions)
    completed_sessions = sum(1 for s in sessions if s.status == 'COMPLETED')
    active_sessions = sum(1 for s in sessions if s.status == 'ACTIVE')

    sessions_data = []
    all_incidents = []
    all_env_checks = []

    for s in sessions:
        s_dict = s.to_dict()
        s_dict['submissions'] = [sub.to_dict() for sub in s.submissions]
        s_dict['total_score'] = sum(sub.score for sub in s.submissions)
        sessions_data.append(s_dict)

        for inc in s.incidents:
            inc_dict = inc.to_dict()
            inc_dict['student_name'] = s.student.name if s.student else ''
            inc_dict['student_reg'] = s.student.register_number if s.student else ''
            all_incidents.append(inc_dict)

        for chk in s.environment_checks:
            chk_dict = chk.to_dict()
            chk_dict['student_name'] = s.student.name if s.student else ''
            all_env_checks.append(chk_dict)

    avg_score = 0
    scored_sessions = [s['total_score'] for s in sessions_data if s['submission_count'] > 0]
    if scored_sessions:
        avg_score = round(sum(scored_sessions) / len(scored_sessions), 1)

    return jsonify({
        'exam': exam.to_dict(),
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'summary': {
            'total_candidates': total_sessions,
            'completed_candidates': completed_sessions,
            'active_candidates': active_sessions,
            'average_score': avg_score,
            'total_incidents': len(all_incidents),
            'pending_reviews': sum(1 for inc in all_incidents if inc.get('review_status') == 'PENDING')
        },
        'sessions': sessions_data,
        'incidents': all_incidents,
        'environment_checks': all_env_checks
    }), 200


@api_bp.route('/exams/<int:exam_id>/report.xlsx', methods=['GET'])
@require_api_key
def get_exam_report_xlsx(exam_id):
    """Per-student scores + infractions as an Excel workbook (fetched and saved by GenerateExamReport.xaml)."""
    exam = db.get_or_404(Exam, exam_id)
    return Response(
        build_exam_workbook(exam),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename=Exam_{exam_id}_Report.xlsx'}
    )


@api_bp.route('/students/import', methods=['POST'])
@require_api_key
def import_students():
    """
    Imports student records from a CSV/Excel or JSON payload parsed by ProctorAdministration workflow.
    Validates required fields, checks duplicates against existing database records and within the batch.
    Never silently overwrites records. Returns a structured import summary.
    """
    payload = request.get_json() or {}
    items = payload.get('students') if isinstance(payload, dict) and 'students' in payload else payload
    if not isinstance(items, list):
        return jsonify({'error': 'Expected an array of student objects under "students" or root array.'}), 400

    imported = 0
    skipped = 0
    invalid = 0
    errors = []

    seen_emails = set()
    seen_regs = set()

    for idx, row in enumerate(items, start=1):
        if not isinstance(row, dict):
            invalid += 1
            errors.append(f"Row {idx}: Invalid format (must be a JSON object).")
            continue

        name = str(row.get('name', '')).strip()
        email = str(row.get('email', '')).strip()
        register_number = str(row.get('register_number', '')).strip()

        if not name or not email or not register_number:
            invalid += 1
            errors.append(f"Row {idx}: Missing name, email, or register_number.")
            continue

        # Check duplicate within the current batch
        if email.lower() in seen_emails or register_number.upper() in seen_regs:
            skipped += 1
            errors.append(f"Row {idx} ({name}): Duplicate within submitted batch.")
            continue

        # Check existing in database
        existing = Student.query.filter(
            (Student.email.ilike(email)) | (Student.register_number.ilike(register_number))
        ).first()

        if existing:
            skipped += 1
            errors.append(f"Row {idx} ({name}): Already registered ({existing.register_number}).")
            continue

        new_student = Student(name=name, email=email, register_number=register_number)
        db.session.add(new_student)
        seen_emails.add(email.lower())
        seen_regs.add(register_number.upper())
        imported += 1

    if imported > 0:
        db.session.commit()

    return jsonify({
        'total_rows': len(items),
        'imported': imported,
        'skipped': skipped,
        'invalid': invalid,
        'errors': errors
    }), 200 if invalid == 0 else 207


# ----------------- AUTOMATION QUEUE & RUN TRACKING -----------------

@api_bp.route('/automation/status', methods=['GET'])
def get_automation_status():
    """Returns the most recent UiPath automation run states for the proctor dashboard."""
    limit = request.args.get('limit', 5, type=int)
    runs = AutomationRun.query.order_by(AutomationRun.id.desc()).limit(limit).all()
    latest_run = runs[0].to_dict() if runs else None
    
    return jsonify({
        'latest_run': latest_run,
        'recent_runs': [r.to_dict() for r in runs]
    }), 200


@api_bp.route('/automation/queue', methods=['GET'])
@require_api_key
def get_queued_automation_task():
    """
    Returns the oldest pending automation run for the UiPath robot listener to process.
    Used when running in SERVE_REQUESTS loop mode.
    """
    pending = AutomationRun.query.filter_by(status='PENDING').order_by(AutomationRun.id.asc()).first()
    if not pending:
        return jsonify({'message': 'No pending tasks in queue', 'task': None}), 200

    return jsonify({'task': pending.to_dict()}), 200


@api_bp.route('/automation/trigger', methods=['POST'])
def trigger_automation():
    """
    Allows the human proctor or student workflow to request a UiPath automation execution.
    Creates a pending AutomationRun.
    """
    data = request.get_json() or {}
    workflow_name = data.get('workflow_name', 'Main')
    mode = data.get('mode', 'FULL_DEMO')
    session_id = data.get('session_id')
    exam_id = data.get('exam_id')

    # If session_id provided, ensure valid
    if session_id:
        db.get_or_404(ExamSession, session_id)
    if exam_id:
        db.get_or_404(Exam, exam_id)

    run = AutomationRun(
        workflow_name=workflow_name,
        mode=mode,
        status='PENDING',
        session_id=session_id,
        exam_id=exam_id,
        started_at=datetime.now(timezone.utc)
    )
    db.session.add(run)
    db.session.commit()

    return jsonify({
        'message': f'Automation run #{run.id} queued for {workflow_name} ({mode})',
        'run': run.to_dict()
    }), 202


@api_bp.route('/automation/runs/<int:run_id>/update', methods=['POST'])
@require_api_key
def update_automation_run(run_id):
    """UiPath robot reports progress, completion, logs, or error status."""
    run = db.get_or_404(AutomationRun, run_id)
    data = request.get_json() or {}

    new_status = data.get('status', run.status).upper()
    if new_status in ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED']:
        run.status = new_status

    if new_status in ['COMPLETED', 'FAILED'] and not run.completed_at:
        run.completed_at = datetime.now(timezone.utc)

    if 'error_message' in data:
        run.error_message = data['error_message']
    if 'log_output' in data:
        run.log_output = (run.log_output or '') + "\n" + str(data['log_output'])
    if 'report_path' in data:
        run.report_path = data['report_path']

    db.session.commit()
    return jsonify({'message': f'Run #{run.id} updated', 'run': run.to_dict()}), 200


@api_bp.route('/reports/download/<path:filename>', methods=['GET'])
def download_report(filename):
    """Allows proctors to securely download generated Excel or PDF examination reports."""
    reports_dir = current_app.config.get('REPORTS_DIR', '')
    if not os.path.isdir(reports_dir):
        return jsonify({'error': 'Reports directory does not exist'}), 404
    
    # Secure filename check
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(reports_dir, safe_filename)
    if not os.path.isfile(file_path):
        return jsonify({'error': f'Report file "{safe_filename}" not found.'}), 404

    return send_from_directory(reports_dir, safe_filename, as_attachment=True)
