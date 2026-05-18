"""
ATOMQUEST — Application Factory
"""
import os
from flask import Flask
from .config import config_map
from .extensions import db, migrate, login_manager, csrf


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['development']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import models so they are registered with SQLAlchemy
    from .models import user, goal, checkin, cycle, audit  # noqa: F401

    # User loader for Flask-Login
    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.employee import employee_bp
    from .routes.manager import manager_bp
    from .routes.admin import admin_bp
    from .routes.reports import reports_bp
    from .routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    # Register context processors
    @app.context_processor
    def inject_globals():
        from .models.cycle import PerformanceCycle
        active_cycle = PerformanceCycle.query.filter_by(is_active=True).first()
        return dict(active_cycle=active_cycle)

    # Root redirect
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == 'manager':
                return redirect(url_for('manager.dashboard'))
            else:
                return redirect(url_for('employee.dashboard'))
        return redirect(url_for('auth.login'))

    return app
