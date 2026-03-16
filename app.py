from pathlib import Path
import sqlite3

from flask import Flask, g, render_template
from markupsafe import Markup, escape


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "pantrypi.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


def nl2br_filter(value):
    if not value:
        return ""
    return Markup(escape(value).replace("\n", Markup("<br>\n")))


def create_app():
    app = Flask(
        __name__,
        instance_relative_config=False,
        static_folder="static",
        template_folder="templates",
    )
    app.config.from_mapping(SECRET_KEY="change-me")

    app.jinja_env.filters["nl2br"] = nl2br_filter

    app.teardown_appcontext(close_db)

    @app.before_request
    def ensure_db_initialized():
        # Lazily create and initialize the DB on first request
        if not DB_PATH.exists():
            init_db()

    # Register blueprints
    from routes.recipes import bp as recipes_bp
    from routes.planner import bp as planner_bp
    from routes.grocery import bp as grocery_bp

    app.register_blueprint(recipes_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(grocery_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True)

