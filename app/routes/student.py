from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Student, Exam, ExamSession, Question, Submission

student_bp = Blueprint('student', __name__)

@student_bp.route('/')
@student_bp.route('/student')
def select_student_exam():
    students = Student.query.order_by(Student.name.asc()).all()
    exams = Exam.query.order_by(Exam.title.asc()).all()
    return render_template('student/select.html', students=students, exams=exams)

@student_bp.route('/student/consent', methods=['GET', 'POST'])
def consent():
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        exam_id = request.form.get('exam_id', type=int)

        if not student_id or not exam_id:
            flash('Please select both a student and an exam.', 'warning')
            return redirect(url_for('student.select_student_exam'))

        student = db.get_or_404(Student, student_id)
        exam = db.get_or_404(Exam, exam_id)

        # Check if already active
        existing_session = ExamSession.query.filter_by(
            student_id=student_id,
            exam_id=exam_id,
            status='ACTIVE'
        ).first()

        if existing_session:
            return redirect(url_for('student.exam_view', session_id=existing_session.id))

        return render_template('student/consent.html', student=student, exam=exam)

    # If accessed directly with query params
    student_id = request.args.get('student_id', type=int)
    exam_id = request.args.get('exam_id', type=int)
    if not student_id or not exam_id:
        return redirect(url_for('student.select_student_exam'))

    student = db.get_or_404(Student, student_id)
    exam = db.get_or_404(Exam, exam_id)
    return render_template('student/consent.html', student=student, exam=exam)

@student_bp.route('/student/start', methods=['POST'])
def start_exam():
    student_id = request.form.get('student_id', type=int)
    exam_id = request.form.get('exam_id', type=int)

    if not student_id or not exam_id:
        flash('Invalid session initiation request.', 'danger')
        return redirect(url_for('student.select_student_exam'))

    student = db.get_or_404(Student, student_id)
    exam = db.get_or_404(Exam, exam_id)

    # Check if there is an existing ACTIVE session
    session = ExamSession.query.filter_by(
        student_id=student_id,
        exam_id=exam_id,
        status='ACTIVE'
    ).first()

    now = datetime.now(timezone.utc)
    if not session:
        # Check if there is an existing NOT_STARTED session
        session = ExamSession.query.filter_by(
            student_id=student_id,
            exam_id=exam_id,
            status='NOT_STARTED'
        ).first()

        if session:
            session.status = 'ACTIVE'
            session.started_at = now
            session.consent_given = True
            session.consent_timestamp = now
            db.session.commit()
        else:
            session = ExamSession(
                student_id=student_id,
                exam_id=exam_id,
                started_at=now,
                status='ACTIVE',
                consent_given=True,
                consent_timestamp=now
            )
            db.session.add(session)
            db.session.commit()

    return redirect(url_for('student.exam_view', session_id=session.id))

@student_bp.route('/student/exam/<int:session_id>')
def exam_view(session_id):
    session = db.get_or_404(ExamSession, session_id)
    if session.status == 'COMPLETED':
        return redirect(url_for('student.completed_view', session_id=session.id))

    exam = session.exam
    questions = exam.questions
    submissions = {sub.question_id: sub for sub in session.submissions}

    return render_template(
        'student/exam.html',
        session=session,
        exam=exam,
        questions=questions,
        submissions=submissions
    )

@student_bp.route('/student/finish/<int:session_id>', methods=['GET', 'POST'])
def finish_exam(session_id):
    session = db.get_or_404(ExamSession, session_id)
    if session.status != 'COMPLETED':
        session.status = 'COMPLETED'
        session.ended_at = datetime.now(timezone.utc)
        db.session.commit()
    return redirect(url_for('student.completed_view', session_id=session.id))

@student_bp.route('/student/completed/<int:session_id>')
def completed_view(session_id):
    session = db.get_or_404(ExamSession, session_id)
    return render_template('student/completed.html', session=session)

@student_bp.route('/student/execute', methods=['POST'])
def execute_code_route():
    from flask import jsonify
    from app.services.code_runner import execute_mock_code
    data = request.get_json() or {}
    code = data.get('code', '')
    language = data.get('language', 'python')
    question_id = data.get('question_id')
    result = execute_mock_code(code=code, language=language, question_id=question_id)
    return jsonify(result), 200

@student_bp.route('/student/submit', methods=['POST'])
def submit_code_route():
    from flask import jsonify
    from app.services.code_runner import execute_mock_code
    data = request.get_json() or {}
    session_id = data.get('session_id')
    question_id = data.get('question_id')
    code = data.get('code', '')
    language = data.get('language', 'python')

    if not session_id or not question_id:
        return jsonify({'success': False, 'error': 'session_id and question_id are required'}), 400

    session = db.get_or_404(ExamSession, session_id)
    question = db.get_or_404(Question, question_id)

    exec_result = execute_mock_code(code=code, language=language, question_id=question_id)

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
    return jsonify({
        'success': True,
        'submission': submission.to_dict(),
        'score': submission.score,
        'output': submission.output
    }), 200

