"""
Scoring Service — Compute progress scores using the 4 formulas.
"""


def compute_score(goal, achievement):
    """
    Compute progress score based on goal unit type.
    
    Formulas:
    - Min (Numeric/%): Achievement ÷ Target  (higher actual = better)
    - Max (Numeric/%): Target ÷ Achievement  (lower actual = better)
    - Timeline: Completion date vs. Deadline
    - Zero-based: If actual == 0 → 100%, else 0%
    """
    if goal.unit_type == 'zero_based':
        if achievement.actual_value is not None and achievement.actual_value == 0:
            return 100.0
        return 0.0

    elif goal.unit_type == 'timeline':
        if achievement.completion_date and goal.target_date:
            if achievement.completion_date <= goal.target_date:
                return 100.0
            days_late = (achievement.completion_date - goal.target_date).days
            # 5% penalty per day late, floor at 0
            return max(0.0, 100.0 - (days_late * 5))
        return 0.0

    elif goal.unit_type in ('numeric', 'percentage'):
        if achievement.actual_value is None:
            return 0.0
        if goal.target_value is None or goal.target_value == 0:
            return 0.0

        # Default: Min formula (Achievement ÷ Target) — higher is better
        ratio = achievement.actual_value / goal.target_value
        score = ratio * 100
        return min(score, 150.0)  # Cap at 150%

    return 0.0


def compute_weighted_score(goals):
    """
    Compute weighted average score across all goals.
    Returns a dict with per-goal scores and overall weighted score.
    """
    results = []
    total_weighted = 0.0
    total_weight = 0

    for goal in goals:
        latest_achievement = None
        if goal.achievements:
            latest_achievement = goal.achievements[-1]  # Most recent quarter

        score = 0.0
        if latest_achievement:
            score = compute_score(goal, latest_achievement)

        weighted = score * (goal.weightage / 100)
        total_weighted += weighted
        total_weight += goal.weightage

        results.append({
            'goal_id': goal.id,
            'title': goal.title,
            'weightage': goal.weightage,
            'raw_score': round(score, 1),
            'weighted_score': round(weighted, 1),
        })

    return {
        'goals': results,
        'overall_score': round(total_weighted, 1),
        'total_weight': total_weight,
    }


def compute_quarter_scores(goals, quarter):
    """Compute scores for a specific quarter."""
    results = []
    total_weighted = 0.0

    for goal in goals:
        achievement = next(
            (a for a in goal.achievements if a.quarter == quarter), None
        )
        score = 0.0
        if achievement:
            score = compute_score(goal, achievement)

        weighted = score * (goal.weightage / 100)
        total_weighted += weighted

        results.append({
            'goal_id': goal.id,
            'title': goal.title,
            'weightage': goal.weightage,
            'actual_value': achievement.actual_value if achievement else None,
            'target_value': goal.target_value,
            'raw_score': round(score, 1),
            'weighted_score': round(weighted, 1),
            'status': goal.status,
        })

    return {
        'quarter': quarter,
        'goals': results,
        'overall_score': round(total_weighted, 1),
    }
