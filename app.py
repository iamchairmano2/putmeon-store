"""
PUT ME ON — Clothing Store
--------------------------
Flask backend for the storefront + admin dashboard.

Product photos are stored on Cloudinary (not on this server), so they
survive redeploys, restarts, and free-tier spin-downs on hosts like Render.

Run locally:
    pip install -r requirements.txt
    (set your Cloudinary environment variables — see README.md)
    python app.py

Then open:
    http://127.0.0.1:5000/            -> storefront
    http://127.0.0.1:5000/admin/login -> admin login

IMPORTANT before you go live (see README.md for the full checklist):
  1. Change ADMIN_USERNAME and ADMIN_PASSWORD below.
  2. Change app.secret_key to a random string.
  3. Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
     as environment variables (never hardcode these in the file).
  4. Change WHATSAPP_NUMBER if it's ever different.
"""

import os
import sqlite3
from datetime import datetime
from functools import wraps

import cloudinary
import cloudinary.uploader
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

# Postgres support. If a DATABASE_URL environment variable is set (Render
# sets this automatically once you attach a PostgreSQL database), the app
# uses Postgres so your product data survives redeploys. If DATABASE_URL
# is NOT set (e.g. running on your own laptop without a database), the app
# falls back to a local SQLite file, just like before.
import psycopg2
import psycopg2.extras

# Optional: load a local .env file if python-dotenv is installed and the
# file exists. This only matters for running on your own computer — on
# Render you'll set these as real environment variables instead.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# CONFIG — the settings you're most likely to want to change
# ---------------------------------------------------------------------------

# Admin login (CHANGE THESE before you deploy the site for real)
ADMIN_USERNAME = "putmeon"
ADMIN_PASSWORD = "changeme123"

# WhatsApp number customers are sent to when they check out.
# Format: country code + number, no "+", no spaces, no leading 0.
WHATSAPP_NUMBER = "233596146157"

# Brand name shown across the site
BRAND_NAME = "PUT ME ON"

# ---------------------------------------------------------------------------
# APP SETUP — you shouldn't need to touch this part
# ---------------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")

# Render (and most hosts) provide the Postgres connection string via
# DATABASE_URL. If it's present, we use Postgres. Otherwise we fall back
# to the local SQLite file above, which is fine for testing on your laptop
# but NOT safe on Render's free tier (that disk gets wiped on redeploy).
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)

app = Flask(__name__)
app.secret_key = "change-this-secret-key-to-something-random"  # CHANGE THIS

ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# Cloudinary configuration — reads from environment variables.
# On Render: set these in the service's "Environment" tab.
# Locally: set them in a .env file (see .env.example) or your shell.
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True,
)


class DBConnection:
    """
    A tiny wrapper so the rest of the app can keep calling
    conn.execute(sql, params).fetchone() / .fetchall() / conn.commit() /
    conn.close() exactly like it did with plain sqlite3 — whether the real
    connection underneath is SQLite (local dev) or Postgres (Render).

    Query strings in the rest of the file use "?" placeholders (SQLite
    style). When running on Postgres, those get swapped to "%s"
    automatically here.
    """

    def __init__(self):
        if USE_POSTGRES:
            self.conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            self.conn = sqlite3.connect(DATABASE)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

    def execute(self, sql, params=()):
        if USE_POSTGRES:
            sql = sql.replace("?", "%s")
        self.cursor.execute(sql, params)
        return self.cursor

    def commit(self):
        self.conn.commit()

    def close(self):
        try:
            self.cursor.close()
        finally:
            self.conn.close()


def get_db():
    return DBConnection()


def init_db():
    conn = get_db()
    if USE_POSTGRES:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                image_url TEXT,
                image_public_id TEXT,
                description TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
    else:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                image_url TEXT,
                image_public_id TEXT,
                description TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
    conn.commit()
    conn.close()


def upload_image(file_storage):
    """
    Upload an image to Cloudinary. Returns (secure_url, public_id), or
    (None, None) if no valid file was given.
    """
    if file_storage and file_storage.filename:
        result = cloudinary.uploader.upload(
            file_storage,
            folder="putmeon_products",
        )
        return result.get("secure_url"), result.get("public_id")
    return None, None


def delete_image(public_id):
    """Remove an image from Cloudinary by its public_id, if one exists."""
    if public_id:
        cloudinary.uploader.destroy(public_id)


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# STOREFRONT (public pages)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    conn = get_db()
    products = conn.execute(
        "SELECT * FROM products ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template(
        "index.html",
        products=products,
        brand_name=BRAND_NAME,
        whatsapp_number=WHATSAPP_NUMBER,
    )


# ---------------------------------------------------------------------------
# ADMIN — login / logout
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Wrong username or password. Try again."
    return render_template("admin_login.html", error=error, brand_name=BRAND_NAME)


@app.route("/admin/logout")
def admin_logout():
    session.pop("logged_in", None)
    return redirect(url_for("admin_login"))


# ---------------------------------------------------------------------------
# ADMIN — dashboard / product management
# ---------------------------------------------------------------------------

@app.route("/admin")
@login_required
def admin_dashboard():
    conn = get_db()
    products = conn.execute(
        "SELECT * FROM products ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template(
        "admin_dashboard.html", products=products, brand_name=BRAND_NAME
    )


@app.route("/admin/add", methods=["POST"])
@login_required
def add_product():
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "").strip()
    description = request.form.get("description", "").strip()
    image = request.files.get("image")

    if not name or not price:
        flash("Product name and price are required.")
        return redirect(url_for("admin_dashboard"))

    try:
        price_value = float(price)
    except ValueError:
        flash("Price must be a number, e.g. 150 or 150.00")
        return redirect(url_for("admin_dashboard"))

    try:
        image_url, public_id = upload_image(image)
    except Exception as exc:
        flash(f"Image upload failed: {exc}")
        return redirect(url_for("admin_dashboard"))

    conn = get_db()
    conn.execute(
        """INSERT INTO products (name, price, image_url, image_public_id, description, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, price_value, image_url, public_id, description, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    flash(f'"{name}" was added.')
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/edit/<int:product_id>", methods=["POST"])
@login_required
def edit_product(product_id):
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "").strip()
    description = request.form.get("description", "").strip()
    image = request.files.get("image")

    try:
        price_value = float(price)
    except ValueError:
        flash("Price must be a number.")
        return redirect(url_for("admin_dashboard"))

    conn = get_db()

    if image and image.filename:
        try:
            new_url, new_public_id = upload_image(image)
        except Exception as exc:
            flash(f"Image upload failed: {exc}")
            conn.close()
            return redirect(url_for("admin_dashboard"))

        old = conn.execute(
            "SELECT image_public_id FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if old and old["image_public_id"]:
            delete_image(old["image_public_id"])

        conn.execute(
            "UPDATE products SET name=?, price=?, description=?, image_url=?, image_public_id=? WHERE id=?",
            (name, price_value, description, new_url, new_public_id, product_id),
        )
    else:
        conn.execute(
            "UPDATE products SET name=?, price=?, description=? WHERE id=?",
            (name, price_value, description, product_id),
        )
    conn.commit()
    conn.close()
    flash(f'"{name}" was updated.')
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    conn = get_db()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if product and product["image_public_id"]:
        delete_image(product["image_public_id"])
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    flash("Product deleted.")
    return redirect(url_for("admin_dashboard"))


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)