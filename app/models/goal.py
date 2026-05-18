"""
Goal, GoalSheet, SharedGoal, and Achievement models.
"""
from datetime import datetime, timezone
from ..extensions import db


class GoalSheet(db.Model):
    """A collection of goals for one employee in one cycle."""
    __tablename__ = 'goal_sheets'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cycle_id = db.Column(db.Integer, db.ForeignKey('performance_cycles.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft')
    # draft, submitted, returned, approved, locked
    submitted_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_locked = db.Column(db.Boolean, default=False)
    return_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    employee = db.relationship('User', foreign_keys=[employee_id], backref='goal_sheets')
    approver = db.relationship('User', foreign_keys=[approved_by])
    cycle = db.relationship('PerformanceCycle', backref='goal_sheets')
    goals = db.relationship('Goal', backref='goal_sheet', cascade='all, delete-orphan',
                            order_by='Goal.order')

    @property
    def total_weightage(self):
        return sum(g.weightage for g in self.goals)

    @property
    def goal_count(self):
        return len(self.goals)

    def __repr__(self):
        return f'<GoalSheet {self.id} - {self.status}>'


class SharedGoal(db.Model):
    """Departmental KPI pushed to multiple employees."""
    __tablename__ = 'shared_goals'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    thrust_area = db.Column(db.String(200), nullable=False)
    unit_type = db.Column(db.String(20), nullable=False)  # numeric, percentage, timeline, zero_based
    target_value = db.Column(db.Float, nullable=True)
    target_date = db.Column(db.Date, nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    primary_owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    department = db.relationship('Department', backref='shared_goals')
    creator = db.relationship('User', foreign_keys=[created_by])
    primary_owner = db.relationship('User', foreign_keys=[primary_owner_id])
    linked_goals = db.relationship('Goal', backref='shared_goal')

    def __repr__(self):
        return f'<SharedGoal {self.title}>'


class Goal(db.Model):
    """Individual goal within a goal sheet."""
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    goal_sheet_id = db.Column(db.Integer, db.ForeignKey('goal_sheets.id'), nullable=False)
    thrust_area = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    unit_type = db.Column(db.String(20), nullable=False)  # numeric, percentage, timeline, zero_based
    target_value = db.Column(db.Float, nullable=True)
    target_date = db.Column(db.Date, nullable=True)
    weightage = db.Column(db.Integer, nullable=False)
    is_shared = db.Column(db.Boolean, default=False)
    shared_goal_id = db.Column(db.Integer, db.ForeignKey('shared_goals.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='not_started')
    # not_started, on_track, completed
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    achievements = db.relationship('Achievement', backref='goal', cascade='all, delete-orphan',
                                   order_by='Achievement.quarter')
    comments = db.relationship('CheckInComment', backref='goal', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Goal {self.title} ({self.weightage}%)>'


class Achievement(db.Model):
    """Quarterly achievement record for a goal."""
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goals.id'), nullable=False)
    quarter = db.Column(db.String(5), nullable=False)  # Q1, Q2, Q3, Q4
    actual_value = db.Column(db.Float, nullable=True)
    completion_date = db.Column(db.Date, nullable=True)
    evidence_notes = db.Column(db.Text, nullable=True)
    computed_score = db.Column(db.Float, nullable=True)
    logged_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    logged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    logger = db.relationship('User', foreign_keys=[logged_by])

    __table_args__ = (
        db.UniqueConstraint('goal_id', 'quarter', name='uq_goal_quarter'),
    )

    def __repr__(self):
        return f'<Achievement Goal#{self.goal_id} {self.quarter}>'
