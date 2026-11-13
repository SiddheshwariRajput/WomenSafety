from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "women_safety_secret_key"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Create database tables
def create_tables():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        contact_name TEXT,
        phone TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        latitude TEXT,
        longitude TEXT,
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


# Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users (name,email,password) VALUES (?,?,?)",
                (name, email, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered"

        conn.close()
        return redirect("/login")

    return render_template("register.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            return redirect("/dashboard")

        return "Invalid email or password"

    return render_template("login.html")


# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    contacts = conn.execute(
        "SELECT * FROM contacts WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    alerts = conn.execute(
        "SELECT * FROM alerts WHERE user_id=? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        name=session["name"],
        contacts=contacts,
        alerts=alerts
    )


# Add trusted contact
@app.route("/add_contact", methods=["POST"])
def add_contact():
    if "user_id" not in session:
        return redirect("/login")

    name = request.form["contact_name"]
    phone = request.form["phone"]

    conn = get_db()
    conn.execute(
        "INSERT INTO contacts (user_id,contact_name,phone) VALUES (?,?,?)",
        (session["user_id"], name, phone)
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# Emergency SOS
@app.route("/send_alert", methods=["POST"])
def send_alert():
    if "user_id" not in session:
        return jsonify({"error": "Please login first"}), 401

    data = request.get_json()
    latitude = str(data.get("latitude", ""))
    longitude = str(data.get("longitude", ""))

    if not latitude or not longitude:
        return jsonify({"error": "Location unavailable"}), 400

    message = (
        "EMERGENCY! I need help. My location: "
        f"https://www.google.com/maps?q={latitude},{longitude}"
    )

    conn = get_db()
    conn.execute(
        """INSERT INTO alerts
        (user_id,latitude,longitude,message)
        VALUES (?,?,?,?)""",
        (session["user_id"], latitude, longitude, message)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": message
    })


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)