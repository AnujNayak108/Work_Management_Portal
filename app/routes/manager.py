"""
Manager routes — Team dashboard, approvals, check-ins.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..extensions import db
from ..models.user import User
from ..models.goal import GoalSheet, Goal
from ..models.cycle import PerformanceCycle
from ..services.goal_service import (
    approve_goal_sheet, return_goal_sheet, edit_goal_inline
)
from ..services.checkin_service import add_checkin_comment
from ..services.scoring_service import compute_weighted_score, compute_quarter_scores

manager_bp = Blueprint('manager', __name__, url_prefix='/manager')


def manager_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('manager', 'admin'):
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


@manager_bp.route('/dashboard')
@login_required
@manager_required
def dashboard():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    team = User.query.filter_by(manager_id=current_user.id, is_active=True).all()

    team_data = []
    for member in team:
        sheet = GoalSheet.query.filter_by(
            employee_id=member.id, cycle_id=cycle.id
        ).first() if cycle else None
        scores = compute_weighted_score(sheet.goals) if sheet and sheet.goals else None
        team_data.append({'user': member, 'sheet': sheet, 'scores': scores})

    pending = GoalSheet.query.filter_by(status='submitted').join(
        User, GoalSheet.employee_id == User.id
    ).filter(User.manager_id == current_user.id).count() if cycle else 0

    return render_template('manager/dashboard.html',
                           cycle=cycle, team_data=team_data, pending_count=pending)


@manager_bp.route('/review/<int:sheet_id>')
@login_required
@manager_required
def review(sheet_id):
    sheet = db.session.get(GoalSheet, sheet_id)
    if not sheet:
        flash('Goal sheet not found.', 'danger')
        return redirect(url_for('manager.dashboard'))

    emp = sheet.employee
    if emp.manager_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('manager.dashboard'))

    return render_template('manager/approval.html', sheet=sheet, employee=emp)


@manager_bp.route('/approve/<int:sheet_id>', methods=['POST'])
@login_required
@manager_required
def approve(sheet_id):
    sheet = db.session.get(GoalSheet, sheet_id)
    if not sheet:
        flash('Goal sheet not found.', 'danger')
        return redirect(url_for('manager.dashboard'))

    approve_goal_sheet(sheet, current_user.id, request.remote_addr)
    flash(f'Goal sheet for {sheet.employee.name} approved and locked.', 'success')
    return redirect(url_for('manager.dashboard'))


@manager_bp.route('/return/<int:sheet_id>', methods=['POST'])
@login_required
@manager_required
def return_sheet(sheet_id):
    sheet = db.session.get(GoalSheet, sheet_id)
    if not sheet:
        flash('Goal sheet not found.', 'danger')
        return redirect(url_for('manager.dashboard'))

    comment = request.form.get('comment', 'Please revise your goals.')
    return_goal_sheet(sheet, current_user.id, comment, request.remote_addr)
    flash(f'Goal sheet returned to {sheet.employee.name}.', 'info')
    return redirect(url_for('manager.dashboard'))


@manager_bp.route('/edit-goal/<int:goal_id>', methods=['POST'])
@login_required
@manager_required
def edit_goal(goal_id):
    goal = db.session.get(Goal, goal_id)
    if not goal:
        flash('Goal not found.', 'danger')
        return redirect(url_for('manager.dashboard'))

    changes = {}
    for field in ('target_value', 'title', 'description'):
        val = request.form.get(field)
        if val is not None:
            changes[field] = val

    edit_goal_inline(goal, changes, current_user.id, request.remote_addr)
    flash('Goal updated.', 'success')
    return redirect(url_for('manager.review', sheet_id=goal.goal_sheet_id))


@manager_bp.route('/checkin/<int:employee_id>')
@login_required
@manager_required
def checkin(employee_id):
    employee = db.session.get(User, employee_id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('manager.dashboard'))

    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    sheet = GoalSheet.query.filter_by(
        employee_id=employee_id, cycle_id=cycle.id
    ).first() if cycle else None

    current_quarter = cycle.current_window() if cycle else None
    quarter_scores = None
    if sheet and current_quarter and current_quarter != 'goal_setting':
        quarter_scores = compute_quarter_scores(sheet.goals, current_quarter)

    return render_template('manager/checkin.html',
                           employee=employee, sheet=sheet,
                           current_quarter=current_quarter,
                           quarter_scores=quarter_scores)


@manager_bp.route('/checkin/<int:goal_id>/comment', methods=['POST'])
@login_required
@manager_required
def add_comment(goal_id):
    goal = db.session.get(Goal, goal_id)
    if not goal:
        flash('Goal not found.', 'danger')
        return redirect(url_for('manager.dashboard'))

    quarter = request.form.get('quarter', 'Q1')
    comment = request.form.get('comment', '')
    rating = request.form.get('rating')

    add_checkin_comment(goal_id, quarter, current_user.id, comment, rating)
    flash('Check-in comment added.', 'success')
    return redirect(url_for('manager.checkin',
                            employee_id=goal.goal_sheet.employee_id))
