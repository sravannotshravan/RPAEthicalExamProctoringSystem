from datetime import datetime, timezone
from app.models import db, Student, Exam, Question, ExamSession, Submission, Incident

def test_create_student(app):
    with app.app_context():
        student = Student(name="Alice Smith", email="alice@test.edu", register_number="REG101")
        db.session.add(student)
        db.session.commit()

        retrieved = Student.query.filter_by(register_number="REG101").first()
        assert retrieved is not None
        assert retrieved.name == "Alice Smith"
        assert retrieved.email == "alice@test.edu"
        data = retrieved.to_dict()
        assert data["register_number"] == "REG101"

def test_create_exam_with_questions(app):
    with app.app_context():
        exam = Exam(title="Data Structures", description="Arrays and Trees", duration_minutes=60)
        db.session.add(exam)
        db.session.commit()

        q1 = Question(
            exam_id=exam.id,
            title="Binary Search",
            description="Implement binary search",
            starter_code="def search(nums, target): pass"
        )
        db.session.add(q1)
        db.session.commit()

        retrieved_exam = db.session.get(Exam, exam.id)
        assert len(retrieved_exam.questions) == 1
        assert retrieved_exam.questions[0].title == "Binary Search"
        assert retrieved_exam.to_dict()["question_count"] == 1

def test_exam_session_and_submission(app):
    with app.app_context():
        student = Student(name="Bob", email="bob@test.edu", register_number="REG102")
        exam = Exam(title="Algorithms", duration_minutes=45)
        db.session.add_all([student, exam])
        db.session.commit()

        q = Question(exam_id=exam.id, title="Factorial", description="Compute n!")
        session = ExamSession(student_id=student.id, exam_id=exam.id, status="ACTIVE")
        db.session.add_all([q, session])
        db.session.commit()

        submission = Submission(
            session_id=session.id,
            question_id=q.id,
            code="def fact(n): return 1 if n<=1 else n*fact(n-1)",
            output="Mock execution successful",
            score=100
        )
        db.session.add(submission)
        db.session.commit()

        retrieved_session = db.session.get(ExamSession, session.id)
        assert len(retrieved_session.submissions) == 1
        assert retrieved_session.submissions[0].score == 100

def test_incident_creation_and_status(app):
    with app.app_context():
        student = Student(name="Charlie", email="charlie@test.edu", register_number="REG103")
        exam = Exam(title="Web Dev", duration_minutes=30)
        db.session.add_all([student, exam])
        db.session.commit()

        session = ExamSession(student_id=student.id, exam_id=exam.id, status="ACTIVE")
        db.session.add(session)
        db.session.commit()

        incident = Incident(
            session_id=session.id,
            incident_type="MULTIPLE_FACES",
            severity="MEDIUM",
            source="CV",
            details="2 faces detected",
            review_status="PENDING"
        )
        db.session.add(incident)
        db.session.commit()

        retrieved_inc = db.session.get(Incident, incident.id)
        assert retrieved_inc.incident_type == "MULTIPLE_FACES"
        assert retrieved_inc.review_status == "PENDING"

        # Update status
        retrieved_inc.review_status = "REVIEWED"
        db.session.commit()
        assert db.session.get(Incident, incident.id).review_status == "REVIEWED"
