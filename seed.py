from app import create_app
from app.models import db, Student, Exam, Question

def seed_database():
    app = create_app()
    with app.app_context():
        print("[*] Seeding database...")
        db.create_all()

        # 1. Seed Demo Students
        students_data = [
            {"name": "Demo Student 1", "email": "demo1@university.edu", "register_number": "REG2026001"},
            {"name": "Demo Student 2", "email": "demo2@university.edu", "register_number": "REG2026002"},
            {"name": "Demo Student 3", "email": "demo3@university.edu", "register_number": "REG2026003"},
        ]

        created_students = []
        for s_data in students_data:
            student = Student.query.filter_by(register_number=s_data["register_number"]).first()
            if not student:
                student = Student(**s_data)
                db.session.add(student)
                print(f"  + Added student: {s_data['name']} ({s_data['register_number']})")
            else:
                print(f"  * Student already exists: {s_data['name']}")
            created_students.append(student)

        db.session.commit()

        # 2. Seed Exam: Python Fundamentals
        exam = Exam.query.filter_by(title="Python Fundamentals").first()
        if not exam:
            exam = Exam(
                title="Python Fundamentals",
                description="Introductory examination assessing algorithmic problem solving in Python: string manipulation, vowel counting, and hash maps.",
                duration_minutes=45
            )
            db.session.add(exam)
            db.session.commit()
            print(f"  + Created exam: {exam.title} (Duration: {exam.duration_minutes} mins)")
        else:
            print(f"  * Exam already exists: {exam.title}")

        # 3. Seed Questions
        questions_data = [
            {
                "title": "Reverse a String",
                "language": "python",
                "description": (
                    "Given an input string `s`, return the reversed string.\n\n"
                    "Example 1:\n"
                    "  Input: s = 'hello'\n"
                    "  Output: 'olleh'\n\n"
                    "Example 2:\n"
                    "  Input: s = 'EthicalProctor'\n"
                    "  Output: 'rotcorPlacihtE'\n\n"
                    "Constraints:\n"
                    "  - 1 <= len(s) <= 10^5\n"
                    "  - s consists of printable ASCII characters."
                ),
                "starter_code": (
                    "def reverse_string(s: str) -> str:\n"
                    "    # Write your solution here\n"
                    "    return s[::-1]\n"
                )
            },
            {
                "title": "Count Vowels in a String",
                "language": "python",
                "description": (
                    "Given a string `s`, count and return the total number of vowels ('a', 'e', 'i', 'o', 'u', case-insensitive).\n\n"
                    "Example 1:\n"
                    "  Input: s = 'examination'\n"
                    "  Output: 6\n\n"
                    "Example 2:\n"
                    "  Input: s = 'Sky'\n"
                    "  Output: 0"
                ),
                "starter_code": (
                    "def count_vowels(s: str) -> int:\n"
                    "    # Write your solution here\n"
                    "    vowels = set('aeiouAEIOU')\n"
                    "    return sum(1 for ch in s if ch in vowels)\n"
                )
            },
            {
                "title": "Two Sum Problem",
                "language": "python",
                "description": (
                    "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to target.\n\n"
                    "Assume that each input would have exactly one solution, and you may not use the same element twice.\n\n"
                    "Example:\n"
                    "  Input: nums = [2, 7, 11, 15], target = 9\n"
                    "  Output: [0, 1]  (Because nums[0] + nums[1] == 9)"
                ),
                "starter_code": (
                    "def two_sum(nums: list[int], target: int) -> list[int]:\n"
                    "    # Write your solution here\n"
                    "    lookup = {}\n"
                    "    for i, num in enumerate(nums):\n"
                    "        complement = target - num\n"
                    "        if complement in lookup:\n"
                    "            return [lookup[complement], i]\n"
                    "        lookup[num] = i\n"
                    "    return []\n"
                )
            }
        ]

        for q_data in questions_data:
            existing_q = Question.query.filter_by(exam_id=exam.id, title=q_data["title"]).first()
            if not existing_q:
                q = Question(
                    exam_id=exam.id,
                    title=q_data["title"],
                    description=q_data["description"],
                    starter_code=q_data["starter_code"],
                    language=q_data["language"]
                )
                db.session.add(q)
                print(f"  + Added question: {q_data['title']}")
            else:
                print(f"  * Question already exists: {q_data['title']}")

        db.session.commit()
        print("[OK] Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
