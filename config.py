import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _load_dotenv(path):
    """Minimal .env loader (KEY=VALUE per line) so secrets never live in source.

    Existing process environment variables always win over values in the file.
    """
    if not os.path.isfile(path):
        return
    with open(path, encoding='utf-8') as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv(os.path.join(BASE_DIR, '.env'))

UIPATH_PROJECT_DIR = os.path.join(BASE_DIR, 'uipath', 'ExamProctoring')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'poc-ethical-proctoring-dev-key-2026')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'exam.db')}"
    )

    # --- UiPath service credential -------------------------------------------------
    # Dedicated API key used ONLY by UiPath workflows (header: X-API-Key).
    # Generated into .env by start.ps1 / uipath/setup_api_key.ps1. Never committed.
    UIPATH_API_KEY = os.environ.get('UIPATH_API_KEY', '')

    # --- Faculty / proctor login ---------------------------------------------------
    FACULTY_PASSWORD = os.environ.get('FACULTY_PASSWORD', 'proctor-demo')

    # --- UiPath integration ----------------------------------------------------------
    UIPATH_PROJECT_DIR = UIPATH_PROJECT_DIR
    # Generated reports must live inside this directory to be downloadable.
    REPORTS_DIR = os.environ.get('REPORTS_DIR', os.path.join(UIPATH_PROJECT_DIR, 'Output'))
    # Uploaded CSV/XLSX files waiting for the UiPath import workflow.
    IMPORT_INBOX_DIR = os.environ.get('IMPORT_INBOX_DIR', os.path.join(UIPATH_PROJECT_DIR, 'Data', 'Inbox'))
    # How Flask hands work to UiPath:
    #   queue  -> requests wait until a UiPath robot running Main.xaml (SERVE_REQUESTS) claims them
    #   robot  -> additionally launch UiRobot.exe execute for each request
    AUTOMATION_LAUNCH_MODE = os.environ.get('AUTOMATION_LAUNCH_MODE', 'queue')
    UIROBOT_PATH = os.environ.get('UIROBOT_PATH', '')
    # A robot listener is considered online if it sent a heartbeat within this window.
    ROBOT_HEARTBEAT_TIMEOUT_SECONDS = int(os.environ.get('ROBOT_HEARTBEAT_TIMEOUT_SECONDS', '45'))
    # A requested run that nobody picks up within this window is reported as unavailable.
    RUN_PICKUP_TIMEOUT_SECONDS = int(os.environ.get('RUN_PICKUP_TIMEOUT_SECONDS', '120'))


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UIPATH_API_KEY = 'test-service-key'
    FACULTY_PASSWORD = 'test-proctor'
    AUTOMATION_LAUNCH_MODE = 'queue'
