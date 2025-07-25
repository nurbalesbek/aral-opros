import os
import json
import psycopg2
from flask import Flask, render_template, request, redirect, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# --- Database connection ----------------------------------------------

def get_db_connection():
    """
    Return a psycopg2 connection to Cloud SQL (via Unix socket) or
    to a local TCP host for development.
    """
    # Required env vars: DB_NAME, DB_USER, DB_PASSWORD
    db_name = os.environ["DB_NAME"]
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASSWORD"]

    # If running in Cloud Run with Cloud SQL, this will be set:
    conn_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    if conn_name:
        # Unix socket path that Cloud SQL Proxy mounts
        host = f"/cloudsql/{conn_name}"
    else:
        # Local development; default host 127.0.0.1
        host = os.environ.get("DB_HOST", "127.0.0.1")

    return psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_pass,
        host=host
    )

# --- Optional: initialize the table if it doesn't exist -------------

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    id SERIAL PRIMARY KEY,
                    country        TEXT,
                    gender         TEXT,
                    age            TEXT,
                    with_children  TEXT,
                    source         TEXT,
                    travel_mode    TEXT,
                    days           TEXT,
                    accommodation  TEXT,
                    suggestions    TEXT,
                    submitted_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

# Run once on startup
init_db()

# --- Load list of countries from JSON -------------------------------

# Assumes a file countries.json in the same directory, containing
# a JSON array of country names, e.g. ["Kazakhstan", "Russia", ...]
try:
    with open("countries.json", encoding="utf-8") as f:
        COUNTRIES = json.load(f)
except FileNotFoundError:
    # Fallback to a hard‑coded list of CIS+Other
    COUNTRIES = [
        "Азербайджан", "Армения", "Беларусь", "Казахстан", "Кыргызстан",
        "Молдова", "Россия", "Таджикистан", "Туркменистан", "Узбекистан",
        "Украина", "Эстония", "Латвия", "Литва", "Грузия", "Другое"
    ]

# --- Flask routes -----------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", countries=COUNTRIES)

@app.route("/submit", methods=["POST"])
def submit():
    fields = [
        "country", "gender", "age", "with_children",
        "source", "travel_mode", "days", "accommodation", "suggestions"
    ]
    data = {field: request.form.get(field, "").strip() for field in fields}

    # Basic validation: require all except suggestions
    if not all(data[f] for f in fields if f != "suggestions"):
        flash("Пожалуйста, заполните все обязательные поля.", "error")
        return redirect("/")

    # Insert into database
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO responses
                      (country, gender, age, with_children, source,
                       travel_mode, days, accommodation, suggestions)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data["country"], data["gender"], data["age"],
                    data["with_children"], data["source"],
                    data["travel_mode"], data["days"],
                    data["accommodation"], data["suggestions"]
                ))
                conn.commit()
    except Exception as e:
        flash(f"Ошибка при сохранении данных: {e}", "error")
        return redirect("/")

    return redirect("/thank_you")

@app.route("/thank_you", methods=["GET"])
def thank_you():
    return render_template("thank_you.html")

# --- Run --------------------------------------------------------------

if __name__ == "__main__":
    # On Cloud Run, PORT is set automatically; locally default to 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
