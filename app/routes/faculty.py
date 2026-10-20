import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, Student, Exam, Question, ExamSession, Incident, AutomationRun

logger = logging.getLogger(__name__)

faculty_bp = Blueprint('faculty', __name__)

def _wants_json():
    """Helper to detect if the caller expects a JSON response (API/AJAX/client)."""
    return (
        request.is_json
        or 'application/json' in request.headers.get('Accept', '')
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.args.get('format') == 'json'
    )


# ----------------- DASHBOARD -----------------

@faculty_bp.route('', methods=['GET'])
@faculty_bp.route('/', methods=['GET'])
@faculty_bp.route('/dashboard', methods=['GET'])
def dashboard():
    total_students = Student.query.count()
    total_exams = Exam.query.count()
    total_sessions = ExamSession.query.count()
    active_sessions = ExamSession.query.filter_by(status='ACTIVE').count()
    pending_incidents = Incident.query.filter_by(review_status='PENDING').count()

    recent_sessions = ExamSession.query.order_by(ExamSession.id.desc()).limit(10).all()
    recent_incidents = Incident.query.order_by(Incident.timestamp.desc()).limit(10).all()
    recent_automation_runs = AutomationRun.query.order_by(AutomationRun.started_at.desc()).limit(5).all()

    if _wants_json():
        return jsonify({
            'success': True,
            'metrics': {
                'total_students': total_students,
                'total_exams': total_exams,
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'pending_incidents': pending_incidents
            },
            'recent_sessions': [s.to_dict() for s in recent_sessions],
            'recent_incidents': [i.to_dict() for i in recent_incidents],
            'recent_automation_runs': [r.to_dict() for r in recent_automation_runs]
        }), 200

    return render_template(
        'faculty/dashboard.html',
        total_students=total_students,
        total_exams=total_exams,
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        pending_incidents=pending_incidents,
        recent_sessions=recent_sessions,
        recent_incidents=recent_incidents,
        recent_automation_runs=recent_automation_runs
    )


# ----------------- EXAMS -----------------

@faculty_bp.route('/exams', methods=['GET'])
def exams():
    all_exams = Exam.query.order_by(Exam.created_at.desc()).all()
    if _wants_json():
        return jsonify([e.to_dict() for e in all_exams]), 200
    return render_template('faculty/exams.html', exams=all_exams)


@faculty_bp.route('/exams', methods=['POST'])
@faculty_bp.route('/exams/create', methods=['POST'])
def create_exam():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    title = (request.form.get('title') or data.get('title') or '').strip()
    description = (request.form.get('description') or data.get('description') or '').strip()
    duration_minutes = request.form.get('duration_minutes', type=int) or data.get('duration_minutes') or 30

    try:
        duration_minutes = int(duration_minutes)
    except (ValueError, TypeError):
        duration_minutes = 30

    if not title:
        if _wants_json():
            return jsonify({'success': False, 'error': 'Exam title is required.'}), 400
        flash('Exam title is required.', 'danger')
        return redirect(url_for('faculty.exams'))

    try:
        exam = Exam(title=title, description=description, duration_minutes=duration_minutes)
        db.session.add(exam)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error creating exam: %s", e)
        if _wants_json():
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error creating exam.', 'danger')
        return redirect(url_for('faculty.exams'))

    if _wants_json():
        return jsonify(exam.to_dict()), 201

    flash(f'Exam "{title}" created successfully.', 'success')
    return redirect(url_for('faculty.exam_detail', exam_id=exam.id))


@faculty_bp.route('/exams/<int:exam_id>', methods=['GET'])
def exam_detail(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    if _wants_json():
        data = exam.to_dict()
        data['questions'] = [q.to_dict() for q in exam.questions]
        return jsonify(data), 200
    return render_template('faculty/exam_detail.html', exam=exam)


@faculty_bp.route('/exams/<int:exam_id>', methods=['PUT', 'PATCH'])
@faculty_bp.route('/exams/<int:exam_id>/edit', methods=['POST', 'PUT', 'PATCH'])
def edit_exam(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    title = request.form.get('title') or data.get('title')
    if title:
        exam.title = title.strip()

    description = request.form.get('description') or data.get('description')
    if description is not None:
        exam.description = description.strip()

    duration = request.form.get('duration_minutes', type=int) or data.get('duration_minutes')
    if duration is not None:
        try:
            exam.duration_minutes = int(duration)
        except (ValueError, TypeError):
            pass

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error updating exam #%s: %s", exam_id, e)
        if _wants_json():
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error updating exam.', 'danger')
        return redirect(url_for('faculty.exam_detail', exam_id=exam.id))

    if _wants_json():
        return jsonify(exam.to_dict()), 200

    flash('Exam updated successfully.', 'success')
    return redirect(url_for('faculty.exam_detail', exam_id=exam.id))


@faculty_bp.route('/exams/<int:exam_id>', methods=['DELETE'])
@faculty_bp.route('/exams/<int:exam_id>/delete', methods=['POST', 'DELETE'])
def delete_exam(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    title = exam.title
    try:
        db.session.delete(exam)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error deleting exam #%s: %s", exam_id, e)
        if _wants_json():
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error deleting exam.', 'danger')
        return redirect(url_for('faculty.exams'))

    if _wants_json():
        return jsonify({'success': True, 'message': f'Exam "{title}" deleted.'}), 200

    flash(f'Exam "{title}" deleted.', 'info')
    return redirect(url_for('faculty.exams'))


# ----------------- QUESTIONS -----------------

@faculty_bp.route('/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    question = db.get_or_404(Question, question_id)
    if _wants_json():
        return jsonify(question.to_dict()), 200
    return redirect(url_for('faculty.exam_detail', exam_id=question.exam_id))


@faculty_bp.route('/exams/<int:exam_id>/questions', methods=['POST'])
@faculty_bp.route('/exams/<int:exam_id>/questions/add', methods=['POST'])
def add_question(exam_id):
    db.get_or_404(Exam, exam_id)
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    title = (request.form.get('title') or data.get('title') or '').strip()
    description = (request.form.get('description') or data.get('description') or '').strip()
    starter_code = request.form.get('starter_code') or data.get('starter_code') or ''
    language = (request.form.get('language') or data.get('language') or 'python').strip()

    if not title or not description:
        if _wants_json():
            return jsonify({'success': False, 'error': 'Question title and description are required.'}), 400
        flash('Question title and description are required.', 'danger')
        return redirect(url_for('faculty.exam_detail', exam_id=exam_id))

    try:
        question = Question(
            exam_id=exam_id,
            title=title,
            description=description,
            starter_code=starter_code or '# Write your code here\n',
            language=language
        )
        db.session.add(question)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error adding question to exam #%s: %s", exam_id, e)
        if _wants_json():
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error adding question.', 'danger')
        return redirect(url_for('faculty.exam_detail', exam_id=exam_id))

    if _wants_json():
        return jsonify(question.to_dict()), 201

    flash('Question added successfully.', 'success')
    return redirect(url_for('faculty.exam_detail', exam_id=exam_id))


@faculty_bp.route('/questions/<int:question_id>', methods=['PUT', 'PATCH'])
@faculty_bp.route('/questions/<int:question_id>/edit', methods=['POST', 'PUT', 'PATCH'])
def edit_question(question_id):
    question = db.get_or_404(Question, question_id)
    exam_id = question.exam_id
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    title = request.form.get('title') or data.get('title')
    if title:
        question.title = title.strip()

    description = request.form.get('description') or data.get('description')
    if description:
        question.description = description.strip()

    starter_code = request.form.get('starter_code') or data.get('starter_code')
    if starter_code is not None:
        question.starter_code = starter_code

    language = request.form.get('language') or data.get('language')
    if language:
        question.language = language.strip()

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error updating question #%s: %s", question_id, e)
        if _wants_json():
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error updating question.', 'danger')
        return redirect(url_for('faculty.exam_detail', exam_id=exam_id))

    if _wants_json():
        return jsonify(question.to_dict()), 200

    flash('Question updated successfully.', 'success')
    return redirect(url_for('faculty.exam_detail', exam_id=exam_id))


@faculty_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@faculty_bp.route('/questions/<int:question_id>/delete', methods=['POST', 'DELETE'])
def delete_question(question_id):
    question = db.get_or_404(Question, question_id)
    exam_id = question.exam_id
    try:
        db.session.delete(question)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error deleting question #%s: %s", question_id, e)
        if _wants_json():
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error deleting question.', 'danger')
        return redirect(url_for('faculty.exam_detail', exam_id=exam_id))

    if _wants_json():
        return jsonify({'success': True, 'message': 'Question deleted.'}), 200

    flash('Question deleted.', 'info')
    return redirect(url_for('faculty.exam_detail', exam_id=exam_id))


# ----------------- STUDENTS -----------------

@faculty_bp.route('/students', methods=['GET'])
def students():
    all_students = Student.query.order_by(Student.name.asc()).all()
    if _wants_json():
        return jsonify([s.to_dict() for s in all_students]), 200
    return render_template('faculty/students.html', students=all_students)


@faculty_bp.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    student = db.get_or_404(Student, student_id)
    if _wants_json():
        return jsonify(student.to_dict()), 200
    return redirect(url_for('faculty.students'))


@faculty_bp.route('/students', methods=['POST'])
@faculty_bp.route('/students/create', methods=['POST'])
def create_student():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    name = (request.form.get('name') or data.get('name') or '').strip()
    email = (request.form.get('email') or data.get('email') or '').strip()
    register_number = (request.form.get('register_number') or data.get('register_number') or '').strip()

    if not name or not email or not register_number:
        if _wants_json():
            return jsonify({'success': False, 'error': 'All fields are required.'}), 400
        flash('All fields are required.', 'danger')
        return redirect(url_for('faculty.students'))

    if Student.query.filter((Student.email == email) | (Student.register_number == register_number)).first():
        if _wants_json():
            return jsonify({'success': False, 'error': 'A student with this email or register number already exists.'}), 409
        flash('A student with this email or register number already exists.', 'warning')
        return redirect(url_for('faculty.students'))

    try:
        student = Student(name=name, email=email, register_number=register_number)
        db.session.add(student)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error registering student: %s", e)
        if _wants_json():
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error registering student.', 'danger')
        return redirect(url_for('faculty.students'))

    if _wants_json():
        return jsonify(student.to_dict()), 201

    flash(f'Student "{name}" registered.', 'success')
    return redirect(url_for('faculty.students'))


@faculty_bp.route('/students/<int:student_id>', methods=['DELETE'])
@faculty_bp.route('/students/<int:student_id>/delete', methods=['POST', 'DELETE'])
def delete_student(student_id):
    student = db.get_or_404(Student, student_id)
    name = student.name
    try:
        db.session.delete(student)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error removing student #%s: %s", student_id, e)
        if _wants_json():
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error removing student.', 'danger')
        return redirect(url_for('faculty.students'))

    if _wants_json():
        return jsonify({'success': True, 'message': f'Student "{name}" removed.'}), 200

    flash(f'Student "{name}" removed.', 'info')
    return redirect(url_for('faculty.students'))


# ----------------- SESSIONS -----------------

@faculty_bp.route('/sessions', methods=['GET'])
def sessions():
    all_sessions = ExamSession.query.order_by(ExamSession.id.desc()).all()
    sessions_json = []
    for s in all_sessions:
        s_data = s.to_dict()
        s_data['incidents'] = [inc.to_dict() for inc in s.incidents]
        sessions_json.append(s_data)

    if _wants_json():
        return jsonify(sessions_json), 200

    return render_template('faculty/sessions.html', sessions=all_sessions, sessions_json=sessions_json)


@faculty_bp.route('/sessions/<int:session_id>', methods=['GET'])
def session_detail(session_id):
    session = db.get_or_404(ExamSession, session_id)
    incidents_json = [inc.to_dict() for inc in session.incidents]

    if _wants_json():
        s_data = session.to_dict()
        s_data['incidents'] = incidents_json
        s_data['submissions'] = [sub.to_dict() for sub in session.submissions]
        return jsonify(s_data), 200

    return render_template('faculty/session_detail.html', session=session, incidents_json=incidents_json)


# ----------------- INCIDENTS -----------------

@faculty_bp.route('/incidents', methods=['GET'])
def incidents():
    status = request.args.get('status')
    severity = request.args.get('severity')
    query = Incident.query
    if status:
        query = query.filter_by(review_status=status.upper())
    if severity:
        query = query.filter_by(severity=severity.upper())
    all_incidents = query.order_by(Incident.timestamp.desc()).all()

    if _wants_json():
        return jsonify([i.to_dict() for i in all_incidents]), 200

    return redirect(url_for('faculty.sessions'))


@faculty_bp.route('/incidents/<int:incident_id>', methods=['GET'])
def get_incident(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    if _wants_json():
        return jsonify(incident.to_dict()), 200
    return redirect(url_for('faculty.session_detail', session_id=incident.session_id))


@faculty_bp.route('/incidents/<int:incident_id>', methods=['PUT', 'PATCH'])
@faculty_bp.route('/incidents/<int:incident_id>/status', methods=['POST', 'PUT', 'PATCH'])
def update_incident_status(incident_id):
    incident = db.get_or_404(Incident, incident_id)
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    status = (request.form.get('status') or data.get('status') or '').strip().upper()

    if status not in ['PENDING', 'REVIEWED', 'DISMISSED']:
        if _wants_json():
            return jsonify({'success': False, 'error': 'Invalid status. Must be PENDING, REVIEWED, or DISMISSED.'}), 400
        flash('Invalid review status. Must be PENDING, REVIEWED, or DISMISSED.', 'danger')
        return redirect(url_for('faculty.session_detail', session_id=incident.session_id))

    try:
        incident.review_status = status
        db.session.commit()
        flash(f'Incident #{incident_id} marked as {status}.', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error updating incident #%s review status: %s", incident_id, e)
        if _wants_json():
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error updating incident status.', 'danger')
        return redirect(url_for('faculty.session_detail', session_id=incident.session_id))

    if _wants_json():
        return jsonify({'success': True, 'incident': incident.to_dict()}), 200

    return redirect(url_for('faculty.session_detail', session_id=incident.session_id))
