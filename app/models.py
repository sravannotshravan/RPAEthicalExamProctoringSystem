from datetime import datetime, timezone
from typing import TYPE_CHECKING, ClassVar, Optional
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

db = SQLAlchemy()

# db.Model is generated at runtime, so type checkers can't see its keyword-argument
# constructor or the Mapped attributes below. Give them a typed stand-in instead.
if TYPE_CHECKING:
    class Model(DeclarativeBase):
        query: ClassVar[Query]
else:
    Model = db.Model

class Student(Model):
    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False)
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    register_number: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False)

    # Relationships
    sessions: Mapped[list['ExamSession']] = relationship('ExamSession', back_populates='student', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'register_number': self.register_number,
            'session_count': len(self.sessions)
        }


class Exam(Model):
    __tablename__ = 'exams'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, default='')
    duration_minutes: Mapped[int] = mapped_column(db.Integer, default=30, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    questions: Mapped[list['Question']] = relationship('Question', back_populates='exam', cascade='all, delete-orphan', order_by='Question.id')
    sessions: Mapped[list['ExamSession']] = relationship('ExamSession', back_populates='exam', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'question_count': len(self.questions)
        }


class Question(Model):
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    exam_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    starter_code: Mapped[Optional[str]] = mapped_column(db.Text, default='')
    language: Mapped[str] = mapped_column(db.String(50), default='python', nullable=False)

    # Relationships
    exam: Mapped['Exam'] = relationship('Exam', back_populates='questions')
    submissions: Mapped[list['Submission']] = relationship('Submission', back_populates='question', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'title': self.title,
            'description': self.description,
            'starter_code': self.starter_code,
            'language': self.language
        }


class ExamSession(Model):
    __tablename__ = 'exam_sessions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    exam_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    student_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    status: Mapped[str] = mapped_column(db.String(20), default='NOT_STARTED', nullable=False)  # NOT_STARTED, ACTIVE, COMPLETED
    consent_given: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    consent_timestamp: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationships
    exam: Mapped['Exam'] = relationship('Exam', back_populates='sessions')
    student: Mapped['Student'] = relationship('Student', back_populates='sessions')
    submissions: Mapped[list['Submission']] = relationship('Submission', back_populates='session', cascade='all, delete-orphan')
    incidents: Mapped[list['Incident']] = relationship('Incident', back_populates='session', cascade='all, delete-orphan', order_by='Incident.timestamp.desc()')
    environment_checks: Mapped[list['EnvironmentCheck']] = relationship('EnvironmentCheck', back_populates='session', cascade='all, delete-orphan', order_by='EnvironmentCheck.checked_at.desc()')

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


class Submission(Model):
    __tablename__ = 'submissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('exam_sessions.id', ondelete='CASCADE'), nullable=False)
    question_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    code: Mapped[str] = mapped_column(db.Text, nullable=False)
    language: Mapped[str] = mapped_column(db.String(50), default='python', nullable=False)
    output: Mapped[Optional[str]] = mapped_column(db.Text, default='')
    score: Mapped[Optional[int]] = mapped_column(db.Integer, default=100)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    session: Mapped['ExamSession'] = relationship('ExamSession', back_populates='submissions')
    question: Mapped['Question'] = relationship('Question', back_populates='submissions')

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


class Incident(Model):
    __tablename__ = 'incidents'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('exam_sessions.id', ondelete='CASCADE'), nullable=False)
    incident_type: Mapped[str] = mapped_column(db.String(50), nullable=False)  # NO_FACE, MULTIPLE_FACES, etc.
    severity: Mapped[str] = mapped_column(db.String(20), default='LOW', nullable=False)  # LOW, MEDIUM, HIGH
    timestamp: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    source: Mapped[str] = mapped_column(db.String(50), default='CV', nullable=False)
    details: Mapped[Optional[str]] = mapped_column(db.Text, default='')
    review_status: Mapped[str] = mapped_column(db.String(20), default='PENDING', nullable=False)  # PENDING, REVIEWED, DISMISSED

    # Relationships
    session: Mapped['ExamSession'] = relationship('ExamSession', back_populates='incidents')

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


class EnvironmentCheck(Model):
    __tablename__ = 'environment_checks'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('exam_sessions.id', ondelete='CASCADE'), nullable=False)
    status: Mapped[str] = mapped_column(db.String(20), default='PASSED', nullable=False)  # PASSED, FLAGGED, FAILED
    internet_status: Mapped[str] = mapped_column(db.String(20), default='OK', nullable=False)
    browser_detected: Mapped[Optional[str]] = mapped_column(db.String(100), default='')
    webcam_status: Mapped[Optional[str]] = mapped_column(db.String(50), default='AVAILABLE')
    microphone_status: Mapped[Optional[str]] = mapped_column(db.String(50), default='AVAILABLE')
    prohibited_processes: Mapped[Optional[str]] = mapped_column(db.Text, default='')  # Comma-separated or JSON list
    summary: Mapped[Optional[str]] = mapped_column(db.Text, default='')
    checked_at: Mapped[datetime] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    session: Mapped['ExamSession'] = relationship('ExamSession', back_populates='environment_checks')

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


class AutomationRun(Model):
    __tablename__ = 'automation_runs'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    workflow_name: Mapped[str] = mapped_column(db.String(100), nullable=False)  # EnvironmentVerification, ExamLifecycle, etc.
    mode: Mapped[str] = mapped_column(db.String(50), default='DEFAULT', nullable=False)
    status: Mapped[str] = mapped_column(db.String(20), default='PENDING', nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    session_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('exam_sessions.id', ondelete='SET NULL'), nullable=True)
    exam_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('exams.id', ondelete='SET NULL'), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(db.Text, default='')
    log_output: Mapped[Optional[str]] = mapped_column(db.Text, default='')
    report_path: Mapped[Optional[str]] = mapped_column(db.Text, default='')

    # Relationships
    session: Mapped[Optional['ExamSession']] = relationship('ExamSession', foreign_keys=[session_id])
    exam: Mapped[Optional['Exam']] = relationship('Exam', foreign_keys=[exam_id])

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

