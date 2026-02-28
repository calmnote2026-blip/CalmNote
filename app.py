from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "secret_key"

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///journal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# =========================
# Models
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

# =========================
# Helper
# =========================

def login_required():
    if "user_id" not in session:
        return False
    return True

# =========================
# Routes
# =========================

@app.route("/")
def home():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("home.html")


@app.route("/add", methods=["POST"])
def add_entry():
    if not login_required():
        return redirect(url_for("login"))

    content = request.form["content"]
    mood = request.form["mood"]

    new_entry = Entry(
        content=content,
        mood=mood,
        user_id=session["user_id"]
    )

    db.session.add(new_entry)
    db.session.commit()

    return redirect(url_for("home"))


@app.route("/history")
def history():
    if not login_required():
        return redirect(url_for("login"))

    entries = Entry.query.filter_by(
        user_id=session["user_id"]
    ).order_by(Entry.date.desc()).all()

    return render_template("history.html", entries=entries)


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    entries = Entry.query.filter_by(
        user_id=session["user_id"]
    ).all()

    mood_count = {}
    for entry in entries:
        mood_count[entry.mood] = mood_count.get(entry.mood, 0) + 1

    return render_template("dashboard.html", mood_count=mood_count)


# =========================
# Auth
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            session["user_id"] = user.id
            return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# Run
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
