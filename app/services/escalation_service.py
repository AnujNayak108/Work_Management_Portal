"""
Escalation Service — Rule-based escalation engine.
"""
from datetime import datetime, timezone, date, timedelta
from flask import current_app
from ..extensions import db
from ..models.user import User
from ..models.goal import GoalSheet
from ..models.cycle import PerformanceCycle
from ..models.audit import Escalation


def check_and_create_escalations():
    """Run escalation checks for submission, approval, and check-in deadlines."""
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    if not cycle:
        return []

    created = []
    today = date.today()
    days_submit = current_app.config.get('ESCALATION_DAYS_SUBMIT', 7)
    days_approve = current_app.config.get('ESCALATION_DAYS_APPROVE', 5)

    # 1. Goal not submitted
    if cycle.is_goal_setting_open():
        deadline = cycle.goal_setting_start + timedelta(days=days_submit)
        if today > deadline:
            for emp in User.query.filter_by(role='employee', is_active=True).all():
                sheet = GoalSheet.query.filter_by(employee_id=emp.id, cycle_id=cycle.id).first()
                if not sheet or sheet.status == 'draft':
                    if not Escalation.query.filter_by(type='goal_not_submitted', target_user_id=emp.id, cycle_id=cycle.id, resolved=False).first():
                        esc = Escalation(type='goal_not_submitted', target_user_id=emp.id, escalated_to_id=emp.manager_id, level=1, cycle_id=cycle.id, due_date=cycle.goal_setting_end)
                        db.session.add(esc)
                        created.append(esc)

    # 2. Goal not approved
    for sheet in GoalSheet.query.filter_by(cycle_id=cycle.id, status='submitted').all():
        if sheet.submitted_at:
            if today > sheet.submitted_at.date() + timedelta(days=days_approve):
                if not Escalation.query.filter_by(type='goal_not_approved', target_user_id=sheet.employee_id, cycle_id=cycle.id, resolved=False).first():
                    emp = db.session.get(User, sheet.employee_id)
                    esc = Escalation(type='goal_not_approved', target_user_id=sheet.employee_id, escalated_to_id=emp.manager_id if emp else None, level=2, cycle_id=cycle.id, due_date=today)
                    db.session.add(esc)
                    created.append(esc)

    db.session.commit()
    return created


def resolve_escalation(escalation_id):
    """Mark an escalation as resolved."""
    esc = db.session.get(Escalation, escalation_id)
    if esc:
        esc.resolved = True
        esc.resolved_at = datetime.now(timezone.utc)
        db.session.commit()
    return esc
