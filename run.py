import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[START] Ethical Exam Proctoring POC server on http://127.0.0.1:{port}")
    print(f"   - Student Portal:   http://127.0.0.1:{port}/student")
    print(f"   - Faculty Portal:   http://127.0.0.1:{port}/faculty")
    app.run(host='127.0.0.1', port=port, debug=True)
