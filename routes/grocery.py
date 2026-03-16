from flask import Blueprint

bp = Blueprint("grocery", __name__, url_prefix="/grocery")


@bp.route("/")
def grocery_home():
    return "Grocery list coming soon", 200

