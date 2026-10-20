"""
Mock Code Execution Service
============================
NOTE: This is a TEMPORARY MOCK execution service for the Proof of Concept.
It simulates the execution and grading of student submissions without running
arbitrary untrusted code on the Flask server.

In the final production architecture, this service will be replaced with a secure
isolated sandbox execution engine such as Judge0 or Docker-based runner.
"""

def execute_mock_code(code: str, language: str = 'python', question_id: int = None) -> dict:
    """
    Simulates code execution and evaluation against test cases.
    """
    cleaned_code = code.strip() if code else ""

    if not cleaned_code:
        return {
            "status": "Wrong Answer",
            "score": 0,
            "output": "Execution Result: No code provided.\nOutput: Empty submission.",
            "is_mock": True,
            "tests_passed": 0,
            "tests_total": 3
        }

    # Basic mock check: if code contains a syntax error indicator or obvious keyword
    if "syntax_error" in cleaned_code.lower():
        return {
            "status": "Syntax Error",
            "score": 0,
            "output": "SyntaxError: invalid syntax on line 1\nExecution stopped.",
            "is_mock": True,
            "tests_passed": 0,
            "tests_total": 3
        }

    # Standard simulated acceptance
    return {
        "status": "Accepted",
        "score": 100,
        "output": (
            "[MOCK SANDBOX EXECUTION]\n"
            "Status: Accepted\n"
            "Test Case 1: PASSED (Execution time: 14ms)\n"
            "Test Case 2: PASSED (Execution time: 12ms)\n"
            "Test Case 3: PASSED (Execution time: 15ms)\n"
            "Memory: 11.2 MB | Score: 100/100\n"
            "Notice: Evaluated via Mock Execution Service for POC."
        ),
        "is_mock": True,
        "tests_passed": 3,
        "tests_total": 3
    }
