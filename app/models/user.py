"""
User and Department models.
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db


class Department(db.Model):
    """Organizational department."""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    head_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    head = db.relationship('User', foreign_keys=[head_id], backref='headed_department')
    members = db.relationship('User', foreign_keys='User.department_id', backref='department', lazy='dynamic')

    def __repr__(self):
        return f'<Department {self.name}>'


class User(UserMixin, db.Model):
    """Application user — Employee, Manager, or Admin."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # employee, manager, admin
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    azure_oid = db.Column(db.String(36), nullable=True)

    manager = db.relationship('User', remote_side=[id], backref='direct_reports')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_employee(self):
        return self.role == 'employee'

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'
