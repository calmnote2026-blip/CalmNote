from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import google.generativeai as genai
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY", "snt_calmnote_final_2026")

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///calmnote.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Cấu hình Gemini API
gemini_key = os.environ.get("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    pin = db.Column(db.String(20), nullable=False)
    entries = db.relationship('Entry', backref='author', lazy=True)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route("/")
def home():
    if "user_id" not in session: return redirect(url_for("login"))
    feedback = session.pop('ai_feedback', None)
    return render_template("index.html", user=session["username"], feedback=feedback)

@app.route("/save", methods=["POST"])
def save():
    if "user_id" not in session: return redirect(url_for("login"))
    content = request.form["content"]
    mood = int(request.form["mood"])
    entry = Entry(content=content, mood=mood, user_id=session["user_id"])
    db.session.add(entry)
    db.session.commit()

    if model:
        try:
            prompt = f"Người dùng vừa viết nhật ký: '{content}' với mức hạnh phúc {mood}/5. Hãy đưa ra một lời phản hồi cực kỳ ấm áp, đồng cảm và ngắn gọn (dưới 40 từ) bằng tiếng Việt."
            response = model.generate_content(prompt)
            session['ai_feedback'] = response.text
        except:
            session['ai_feedback'] = "Mình đã lắng nghe câu chuyện của bạn. Cố gắng lên nhé! ✨"
    return redirect(url_for("home"))

@app.route("/history")
def history():
    if "user_id" not in session: return redirect(url_for("login"))
    entries = Entry.query.filter_by(user_id=session["user_id"]).order_by(Entry.date.desc()).all()
    # Dữ liệu cho biểu đồ
    chart_data = Entry.query.filter_by(user_id=session["user_id"]).order_by(Entry.date.asc()).all()
    dates = [e.date.strftime("%d/%m") for e in chart_data][-10:]
    moods = [e.mood for e in chart_data][-10:]
    return render_template("history.html", entries=entries, dates=dates, moods=moods)

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "user_id" not in session: return redirect(url_for("login"))
    if request.method == "POST":
        if not model: return jsonify({"reply": "AI chưa sẵn sàng."})
        user_msg = request.json.get("message")
        try:
            res = model.generate_content(f"Bạn là một người bạn tri kỷ, thấu hiểu. Hãy trò chuyện chân thành với: {user_msg}")
            return jsonify({"reply": res.text})
        except:
            return jsonify({"reply": "Mình đang lắng nghe, bạn nói tiếp đi..."})
    return render_template("chat.html", user=session["username"])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"], pin=request.form["pin"]).first()
        if user:
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("home"))
        flash("Sai thông tin đăng nhập!")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if User.query.filter_by(username=request.form["username"]).first():
            flash("Tên đã tồn tại!")
        else:
            new_u = User(username=request.form["username"], pin=request.form["pin"])
            db.session.add(new_u)
            db.session.commit()
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
