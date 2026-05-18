"""
Employee routes — Goal drafting, achievement entry, status updates.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from ..extensions import db
from ..models.goal import GoalSheet, Goal, SharedGoal
from ..models.cycle import PerformanceCycle
from ..services.goal_service import (
    create_goal_sheet, update_goal_sheet, submit_goal_sheet, GoalValidationError
)
from ..services.checkin_service import log_achievement
from ..services.scoring_service import compute_weighted_score

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


def employee_required(f):
    """Decorator to ensure user is an employee."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('employee', 'manager'):
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


@employee_bp.route('/dashboard')
@login_required
@employee_required
def dashboard():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    sheet = None
    scores = None
    if cycle:
        sheet = GoalSheet.query.filter_by(
            employee_id=current_user.id, cycle_id=cycle.id
        ).first()
        if sheet and sheet.goals:
            scores = compute_weighted_score(sheet.goals)

    return render_template('employee/dashboard.html',
                           cycle=cycle, sheet=sheet, scores=scores)


@employee_bp.route('/goals/new', methods=['GET', 'POST'])
@login_required
@employee_required
def goal_form():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    if not cycle:
        flash('No active performance cycle. Contact Admin.', 'warning')
        return redirect(url_for('employee.dashboard'))

    # Check for existing sheet
    existing = GoalSheet.query.filter_by(
        employee_id=current_user.id, cycle_id=cycle.id
    ).first()
    if existing and existing.status in ('approved', 'locked'):
        flash('Your goals are already approved and locked.', 'info')
        return redirect(url_for('employee.view_goals', sheet_id=existing.id))

    # Get shared goals for this employee's department
    shared_goals = []
    if current_user.department_id:
        shared_goals = SharedGoal.query.filter_by(
            department_id=current_user.department_id
        ).all()

    if request.method == 'POST':
        goals_data = _parse_goals_from_form(request.form)
        try:
            if existing and existing.status in ('draft', 'returned'):
                update_goal_sheet(existing, goals_data)
                flash('Goal sheet updated.', 'success')
                return redirect(url_for('employee.view_goals', sheet_id=existing.id))
            else:
                sheet = create_goal_sheet(current_user.id, cycle.id, goals_data)
                flash('Goal sheet created.', 'success')
                return redirect(url_for('employee.view_goals', sheet_id=sheet.id))
        except GoalValidationError as e:
            flash(str(e), 'danger')

    return render_template('employee/goal_form.html',
                           cycle=cycle, sheet=existing, shared_goals=shared_goals)


@employee_bp.route('/goals/<int:sheet_id>')
@login_required
@employee_required
def view_goals(sheet_id):
    sheet = db.session.get(GoalSheet, sheet_id)
    if not sheet or sheet.employee_id != current_user.id:
        flash('Goal sheet not found.', 'danger')
        return redirect(url_for('employee.dashboard'))

    scores = compute_weighted_score(sheet.goals) if sheet.goals else None
    return render_template('employee/dashboard.html',
                           cycle=sheet.cycle, sheet=sheet, scores=scores)


@employee_bp.route('/goals/<int:sheet_id>/submit', methods=['POST'])
@login_required
@employee_required
def submit_goals(sheet_id):
    sheet = db.session.get(GoalSheet, sheet_id)
    if not sheet or sheet.employee_id != current_user.id:
        flash('Goal sheet not found.', 'danger')
        return redirect(url_for('employee.dashboard'))
    try:
        submit_goal_sheet(sheet)
        flash('Goal sheet submitted for approval!', 'success')
    except GoalValidationError as e:
        flash(str(e), 'danger')
    return redirect(url_for('employee.dashboard'))


@employee_bp.route('/achievement/<int:goal_id>', methods=['GET', 'POST'])
@login_required
@employee_required
def achievement(goal_id):
    goal = db.session.get(Goal, goal_id)
    if not goal or goal.goal_sheet.employee_id != current_user.id:
        flash('Goal not found.', 'danger')
        return redirect(url_for('employee.dashboard'))

    cycle = goal.goal_sheet.cycle
    current_quarter = cycle.current_window() if cycle else None

    if request.method == 'POST':
        quarter = request.form.get('quarter', current_quarter)
        actual_value = request.form.get('actual_value')
        completion_date_str = request.form.get('completion_date')
        evidence = request.form.get('evidence_notes', '')
        status = request.form.get('status', goal.status)

        actual_val = float(actual_value) if actual_value else None
        comp_date = None
        if completion_date_str:
            comp_date = date.fromisoformat(completion_date_str)

        log_achievement(goal, quarter, actual_val, comp_date, evidence, current_user.id)
        goal.status = status
        db.session.commit()
        flash('Achievement logged!', 'success')
        return redirect(url_for('employee.dashboard'))

    return render_template('employee/achievement.html',
                           goal=goal, current_quarter=current_quarter)


@employee_bp.route('/goals/<int:goal_id>/status', methods=['POST'])
@login_required
@employee_required
def update_status(goal_id):
    goal = db.session.get(Goal, goal_id)
    if not goal or goal.goal_sheet.employee_id != current_user.id:
        flash('Goal not found.', 'danger')
        return redirect(url_for('employee.dashboard'))

    new_status = request.form.get('status')
    if new_status in ('not_started', 'on_track', 'completed'):
        goal.status = new_status
        db.session.commit()
        flash('Status updated.', 'success')

    return redirect(url_for('employee.dashboard'))


def _parse_goals_from_form(form):
    """Parse goal data from a multi-row form submission."""
    goals = []
    i = 0
    while True:
        title = form.get(f'goals-{i}-title')
        if title is None:
            break
        goal_data = {
            'title': title,
            'thrust_area': form.get(f'goals-{i}-thrust_area', ''),
            'description': form.get(f'goals-{i}-description', ''),
            'unit_type': form.get(f'goals-{i}-unit_type', 'numeric'),
            'target_value': form.get(f'goals-{i}-target_value', ''),
            'target_date': None,
            'weightage': form.get(f'goals-{i}-weightage', '10'),
            'is_shared': form.get(f'goals-{i}-is_shared') == 'true',
            'shared_goal_id': form.get(f'goals-{i}-shared_goal_id') or None,
        }
        td = form.get(f'goals-{i}-target_date')
        if td:
            goal_data['target_date'] = date.fromisoformat(td)
        goals.append(goal_data)
        i += 1
    return goals
