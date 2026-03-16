from flask import Blueprint, redirect, render_template, request, url_for, abort

from app import get_db

bp = Blueprint("recipes", __name__, url_prefix="/recipes")


@bp.route("/")
def list_recipes():
    db = get_db()
    recipes = db.execute(
        """
        SELECT r.id,
               r.title,
               r.description,
               r.prep_time_min,
               r.cook_time_min,
               r.servings,
               GROUP_CONCAT(t.name, ', ') AS tags
        FROM recipes r
        LEFT JOIN recipe_tags rt ON rt.recipe_id = r.id
        LEFT JOIN tags t ON t.id = rt.tag_id
        GROUP BY r.id
        ORDER BY r.created_at DESC
        """
    ).fetchall()
    return render_template("recipes/list.html", recipes=recipes)


@bp.route("/<int:recipe_id>")
def recipe_detail(recipe_id: int):
    db = get_db()
    recipe = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()
    if recipe is None:
        abort(404)

    ingredients = db.execute(
        """
        SELECT *
        FROM ingredients
        WHERE recipe_id = ?
        ORDER BY sort_order, id
        """,
        (recipe_id,),
    ).fetchall()

    tags = db.execute(
        """
        SELECT t.name
        FROM tags t
        JOIN recipe_tags rt ON rt.tag_id = t.id
        WHERE rt.recipe_id = ?
        ORDER BY t.name
        """,
        (recipe_id,),
    ).fetchall()

    return render_template(
        "recipes/detail.html",
        recipe=recipe,
        ingredients=ingredients,
        tags=[t["name"] for t in tags],
    )


@bp.route("/new", methods=["GET", "POST"])
def create_recipe():
    db = get_db()
    if request.method == "POST":
        form = request.form
        title = form.get("title", "").strip()
        instructions = form.get("instructions", "").strip()

        if not title or not instructions:
            return render_template(
                "recipes/edit.html",
                error="Title and instructions are required.",
                recipe=None,
                ingredients=[],
            )

        cur = db.execute(
            """
            INSERT INTO recipes (title, description, prep_time_min, cook_time_min, servings, instructions)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                form.get("description", "").strip() or None,
                _int_or_none(form.get("prep_time_min")),
                _int_or_none(form.get("cook_time_min")),
                _int_or_none(form.get("servings")) or 4,
                instructions,
            ),
        )
        recipe_id = cur.lastrowid

        _upsert_ingredients(db, recipe_id, form)
        _upsert_tags(db, recipe_id, form.get("tags", ""))
        db.commit()

        return redirect(url_for("recipes.recipe_detail", recipe_id=recipe_id))

    return render_template("recipes/edit.html", recipe=None, ingredients=[])


@bp.route("/<int:recipe_id>/edit", methods=["GET", "POST"])
def edit_recipe(recipe_id: int):
    db = get_db()
    recipe = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()
    if recipe is None:
        abort(404)

    if request.method == "POST":
        form = request.form
        title = form.get("title", "").strip()
        instructions = form.get("instructions", "").strip()

        if not title or not instructions:
            ingredients = db.execute(
                "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order, id",
                (recipe_id,),
            ).fetchall()
            tags = db.execute(
                """
                SELECT t.name
                FROM tags t
                JOIN recipe_tags rt ON rt.tag_id = t.id
                WHERE rt.recipe_id = ?
                ORDER BY t.name
                """,
                (recipe_id,),
            ).fetchall()
            return render_template(
                "recipes/edit.html",
                error="Title and instructions are required.",
                recipe=recipe,
                ingredients=ingredients,
                tags_csv=", ".join(t["name"] for t in tags),
            )

        db.execute(
            """
            UPDATE recipes
            SET title = ?, description = ?, prep_time_min = ?, cook_time_min = ?,
                servings = ?, instructions = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                title,
                form.get("description", "").strip() or None,
                _int_or_none(form.get("prep_time_min")),
                _int_or_none(form.get("cook_time_min")),
                _int_or_none(form.get("servings")) or recipe["servings"],
                instructions,
                recipe_id,
            ),
        )

        db.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))
        _upsert_ingredients(db, recipe_id, form)

        db.execute("DELETE FROM recipe_tags WHERE recipe_id = ?", (recipe_id,))
        _upsert_tags(db, recipe_id, form.get("tags", ""))
        db.commit()

        return redirect(url_for("recipes.recipe_detail", recipe_id=recipe_id))

    ingredients = db.execute(
        "SELECT * FROM ingredients WHERE recipe_id = ? ORDER BY sort_order, id",
        (recipe_id,),
    ).fetchall()
    tags = db.execute(
        """
        SELECT t.name
        FROM tags t
        JOIN recipe_tags rt ON rt.tag_id = t.id
        WHERE rt.recipe_id = ?
        ORDER BY t.name
        """,
        (recipe_id,),
    ).fetchall()
    return render_template(
        "recipes/edit.html",
        recipe=recipe,
        ingredients=ingredients,
        tags_csv=", ".join(t["name"] for t in tags),
    )


@bp.route("/<int:recipe_id>/delete", methods=["POST"])
def delete_recipe(recipe_id: int):
    db = get_db()
    db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    db.commit()
    return redirect(url_for("recipes.list_recipes"))


def _int_or_none(value):
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _upsert_ingredients(db, recipe_id: int, form):
    names = form.getlist("ingredient_name")
    quantities = form.getlist("ingredient_quantity")
    units = form.getlist("ingredient_unit")
    categories = form.getlist("ingredient_category")

    for idx, name in enumerate(names):
        name = name.strip()
        if not name:
            continue
        qty = quantities[idx].strip() if idx < len(quantities) else ""
        unit = units[idx].strip() if idx < len(units) else ""
        category = categories[idx].strip() if idx < len(categories) else ""
        db.execute(
            """
            INSERT INTO ingredients (recipe_id, name, quantity, unit, category, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                recipe_id,
                name,
                float(qty) if qty else None,
                unit or None,
                category or "other",
                idx,
            ),
        )


def _upsert_tags(db, recipe_id: int, tags_csv: str):
    tags = [t.strip() for t in tags_csv.split(",") if t.strip()]
    for tag_name in tags:
        cur = db.execute(
            "INSERT OR IGNORE INTO tags (name) VALUES (?)",
            (tag_name,),
        )
        if cur.lastrowid:
            tag_id = cur.lastrowid
        else:
            tag_row = db.execute(
                "SELECT id FROM tags WHERE name = ?",
                (tag_name,),
            ).fetchone()
            if not tag_row:
                continue
            tag_id = tag_row["id"]
        db.execute(
            "INSERT OR IGNORE INTO recipe_tags (recipe_id, tag_id) VALUES (?, ?)",
            (recipe_id, tag_id),
        )

