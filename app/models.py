from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    register_number = db.Column(db.String(64), unique=True, nullable=False)

    # Relationships
    sessions = db.relationship('ExamSession', back_populates='student', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'register_number': self.register_number,
            'session_count': len(self.sessions)
        }


class Exam(db.Model):
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    duration_minutes = db.Column(db.Integer, default=30, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    questions = db.relationship('Question', back_populates='exam', cascade='all, delete-orphan', order_by='Question.id')
    sessions = db.relationship('ExamSession', back_populates='exam', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'question_count': len(self.questions)
        }


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    starter_code = db.Column(db.Text, default='')
    language = db.Column(db.String(50), default='python', nullable=False)

    # Relationships
    exam = db.relationship('Exam', back_populates='questions')
    submissions = db.relationship('Submission', back_populates='question', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'title': self.title,
            'description': self.description,
            'starter_code': self.starter_code,
            'language': self.language
        }


class ExamSession(db.Model):
    __tablename__ = 'exam_sessions'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='NOT_STARTED', nullable=False)  # NOT_STARTED, ACTIVE, COMPLETED
    consent_given = db.Column(db.Boolean, default=False, nullable=False)
    consent_timestamp = db.Column(db.DateTime, nullable=True)

    # Relationships
    exam = db.relationship('Exam', back_populates='sessions')
    student = db.relationship('Student', back_populates='sessions')
    submissions = db.relationship('Submission', back_populates='session', cascade='all, delete-orphan')
    incidents = db.relationship('Incident', back_populates='session', cascade='all, delete-orphan', order_by='Incident.timestamp.desc()')
    environment_checks = db.relationship('EnvironmentCheck', back_populates='session', cascade='all, delete-orphan', order_by='EnvironmentCheck.checked_at.desc()')

    def to_dict(self):
        latest_check = self.environment_checks[0].to_dict() if self.environment_checks else None
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'exam_title': self.exam.title if self.exam else None,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_reg': self.student.register_number if self.student else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'status': self.status,
            'consent_given': self.consent_given,
            'consent_timestamp': self.consent_timestamp.isoformat() if self.consent_timestamp else None,
            'incident_count': len(self.incidents),
            'submission_count': len(self.submissions),
            'environment_check_status': latest_check['status'] if latest_check else 'NOT_CHECKED',
            'latest_environment_check': latest_check
        }


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_sessions.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), default='python', nullable=False)
    output = db.Column(db.Text, default='')
    score = db.Column(db.Integer, default=100)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    session = db.relationship('ExamSession', back_populates='submissions')
    question = db.relationship('Question', back_populates='submissions')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'question_id': self.question_id,
            'question_title': self.question.title if self.question else None,
            'code': self.code,
            'language': self.language,
            'output': self.output,
            'score': self.score,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }


class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_sessions.id', ondelete='CASCADE'), nullable=False)
    incident_type = db.Column(db.String(50), nullable=False)  # NO_FACE, MULTIPLE_FACES, etc.
    severity = db.Column(db.String(20), default='LOW', nullable=False)  # LOW, MEDIUM, HIGH
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    source = db.Column(db.String(50), default='CV', nullable=False)
    details = db.Column(db.Text, default='')
    review_status = db.Column(db.String(20), default='PENDING', nullable=False)  # PENDING, REVIEWED, DISMISSED

    # Relationships
    session = db.relationship('ExamSession', back_populates='incidents')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'incident_type': self.incident_type,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source': self.source,
            'details': self.details,
            'review_status': self.review_status
        }


class EnvironmentCheck(db.Model):
    __tablename__ = 'environment_checks'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_sessions.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='PASSED', nullable=False)  # PASSED, FLAGGED, FAILED
    internet_status = db.Column(db.String(20), default='OK', nullable=False)
    browser_detected = db.Column(db.String(100), default='')
    webcam_status = db.Column(db.String(50), default='AVAILABLE')
    microphone_status = db.Column(db.String(50), default='AVAILABLE')
    prohibited_processes = db.Column(db.Text, default='')  # Comma-separated or JSON list
    summary = db.Column(db.Text, default='')
    checked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    session = db.relationship('ExamSession', back_populates='environment_checks')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'status': self.status,
            'internet_status': self.internet_status,
            'browser_detected': self.browser_detected,
            'webcam_status': self.webcam_status,
            'microphone_status': self.microphone_status,
            'prohibited_processes': self.prohibited_processes,
            'summary': self.summary,
            'checked_at': self.checked_at.isoformat() if self.checked_at else None
        }


class AutomationRun(db.Model):
    __tablename__ = 'automation_runs'

    id = db.Column(db.Integer, primary_key=True)
    workflow_name = db.Column(db.String(100), nullable=False)  # EnvironmentVerification, ExamLifecycle, etc.
    mode = db.Column(db.String(50), default='DEFAULT', nullable=False)
    status = db.Column(db.String(20), default='PENDING', nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    session_id = db.Column(db.Integer, db.ForeignKey('exam_sessions.id', ondelete='SET NULL'), nullable=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='SET NULL'), nullable=True)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, default='')
    log_output = db.Column(db.Text, default='')
    report_path = db.Column(db.Text, default='')

    # Relationships
    session = db.relationship('ExamSession', foreign_keys=[session_id])
    exam = db.relationship('Exam', foreign_keys=[exam_id])

    def to_dict(self):
        return {
            'id': self.id,
            'workflow_name': self.workflow_name,
            'mode': self.mode,
            'status': self.status,
            'session_id': self.session_id,
            'exam_id': self.exam_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'log_output': self.log_output,
            'report_path': self.report_path
        }

