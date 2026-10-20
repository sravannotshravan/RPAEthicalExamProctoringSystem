import os
from flask import Flask
from config import Config
from app.models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure the instance folder exists
    instance_path = os.path.join(app.root_path, '..', 'instance')
    os.makedirs(instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.api import api_bp
    from app.routes.monitoring import monitoring_bp
    from app.routes.student import student_bp
    from app.routes.faculty import faculty_bp

    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(monitoring_bp, url_prefix='/api/monitor')
    app.register_blueprint(student_bp)
    app.register_blueprint(faculty_bp, url_prefix='/faculty')

    with app.app_context():
        db.create_all()

    return app
