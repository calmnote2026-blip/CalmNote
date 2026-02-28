from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "snt_calmnote_v4_final"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calmnote.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ===== OpenAI Client =====
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ===== Database Models =====
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    pin = db.Column(db.String(10), nullable=False)
    entries = db.relationship('Entry', backref='author', lazy=True)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()

# ================= ROUTES =================

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    entries = Entry.query.filter_by(user_id=session['user_id']).order_by(Entry.date.desc()).all()
    chart_data = Entry.query.filter_by(user_id=session['user_id']).order_by(Entry.date.asc()).all()

    dates = [e.date.strftime("%d/%m") for e in chart_data][-7:]
    moods = [e.mood for e in chart_data][-7:]

    return render_template(
        'index.html',
        user=session['username'],
        entries=entries,
        dates=dates,
        moods=moods
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            pin=request.form['pin']
        ).first()

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))

        flash("Sai thông tin!")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            new_user = User(
                username=request.form['username'],
                pin=request.form['pin']
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except:
            flash("Tên đã tồn tại!")

    return render_template('register.html')


@app.route('/save', methods=['POST'])
def save():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    new_entry = Entry(
        content=request.form['content'],
        mood=int(request.form['mood']),
        user_id=session['user_id']
    )

    db.session.add(new_entry)
    db.session.commit()

    return redirect(url_for('home'))


# ====== CHAT PAGE ======
@app.route('/ai-chat')
def ai_chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('chat.html', user=session['username'])


# ====== CHAT API (NEW) ======
@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({"reply": "Bạn cần đăng nhập trước nhé."})

    user_message = request.json.get("message")

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""
Bạn là một người bạn nữ dịu dàng, tinh tế và biết lắng nghe.
Hãy trò chuyện tự nhiên, ấm áp và thấu hiểu.
Người dùng tên là {session['username']}.
"""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.8
        )

        reply = completion.choices[0].message.content

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": "Mình hơi mệt một chút rồi... bạn thử lại nhé."})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
