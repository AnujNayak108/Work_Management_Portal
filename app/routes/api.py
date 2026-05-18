"""
JSON API routes — AJAX endpoints for dashboards, validation, analytics.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..extensions import db, csrf
from ..models.user import User, Department
from ..models.goal import GoalSheet, Goal, Achievement
from ..models.cycle import PerformanceCycle
from ..services.goal_service import validate_goals
from ..services.scoring_service import compute_weighted_score, compute_quarter_scores

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/goals/validate', methods=['POST'])
@login_required
def validate_goals_api():
    data = request.get_json()
    if not data or 'goals' not in data:
        return jsonify({'valid': False, 'errors': ['No data provided.']}), 400

    errors = validate_goals(data['goals'])
    return jsonify({'valid': len(errors) == 0, 'errors': errors})


@api_bp.route('/goals/<int:sheet_id>')
@login_required
def get_goals(sheet_id):
    sheet = db.session.get(GoalSheet, sheet_id)
    if not sheet:
        return jsonify({'error': 'Not found'}), 404

    goals = []
    for g in sheet.goals:
        goals.append({
            'id': g.id, 'title': g.title, 'thrust_area': g.thrust_area,
            'unit_type': g.unit_type, 'target_value': g.target_value,
            'weightage': g.weightage, 'status': g.status,
            'is_shared': g.is_shared,
        })

    return jsonify({
        'sheet_id': sheet.id, 'status': sheet.status,
        'total_weightage': sheet.total_weightage,
        'goals': goals,
    })


@api_bp.route('/dashboard-data')
@login_required
def dashboard_data():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    departments = Department.query.all()
    dept_stats = []
    for dept in departments:
        members = User.query.filter_by(department_id=dept.id, is_active=True).all()
        total = len(members)
        approved = 0
        for m in members:
            s = GoalSheet.query.filter_by(employee_id=m.id, cycle_id=cycle.id, status='approved').first()
            if s:
                approved += 1
        dept_stats.append({
            'name': dept.name, 'total': total, 'approved': approved,
            'rate': round(approved / total * 100, 1) if total > 0 else 0
        })

    return jsonify({'departments': dept_stats, 'cycle': cycle.name})


@api_bp.route('/analytics/trends')
@login_required
def analytics_trends():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    trends = {}
    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
        sheets = GoalSheet.query.filter_by(cycle_id=cycle.id, status='approved').all()
        scores = []
        for sheet in sheets:
            qs = compute_quarter_scores(sheet.goals, q)
            if qs['overall_score'] > 0:
                scores.append(qs['overall_score'])
        trends[q] = round(sum(scores) / len(scores), 1) if scores else 0

    return jsonify({'trends': trends, 'cycle': cycle.name})


@api_bp.route('/analytics/heatmap')
@login_required
def analytics_heatmap():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    heatmap = []
    sheets = GoalSheet.query.filter_by(cycle_id=cycle.id).all()
    for sheet in sheets:
        row = {'employee': sheet.employee.name, 'quarters': {}}
        for q in ['Q1', 'Q2', 'Q3', 'Q4']:
            ach_count = sum(1 for g in sheet.goals if any(a.quarter == q for a in g.achievements))
            total = len(sheet.goals)
            row['quarters'][q] = round(ach_count / total * 100, 0) if total > 0 else 0
        heatmap.append(row)

    return jsonify({'heatmap': heatmap})


@api_bp.route('/analytics/distribution')
@login_required
def analytics_distribution():
    cycle = PerformanceCycle.query.filter_by(is_active=True).first()
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    thrust_areas = {}
    goals = Goal.query.join(GoalSheet).filter(GoalSheet.cycle_id == cycle.id).all()
    for g in goals:
        ta = g.thrust_area
        thrust_areas[ta] = thrust_areas.get(ta, 0) + 1

    return jsonify({'distribution': thrust_areas})
