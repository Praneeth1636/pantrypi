from flask import Blueprint

bp = Blueprint("planner", __name__, url_prefix="/planner")


@bp.route("/")
def planner_home():
    return "Meal planner coming soon", 200

