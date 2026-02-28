from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, random

app = Flask(__name__)
app.secret_key = "snt_calmnote_2026_final"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calmnote.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Cấu trúc Database ---
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

# --- Các đường dẫn (Routes) ---
@app.route('/')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', user=session['username'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            new_user = User(username=request.form['username'], pin=request.form['pin'])
            db.session.add(new_user)
            db.session.commit()
            flash("Đăng ký thành công! Mời bạn đăng nhập.")
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash("Tên đăng nhập đã tồn tại!")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], pin=request.form['pin']).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        flash("Sai tên đăng nhập hoặc mã PIN!")
    return render_template('login.html')

@app.route('/save', methods=['POST'])
def save():
    if 'user_id' not in session: return redirect(url_for('login'))
    mood_val = int(request.form['mood'])
    new_entry = Entry(content=request.form['content'], mood=mood_val, user_id=session['user_id'])
    db.session.add(new_entry)
    db.session.commit()
    
    advices = [
        "Cảm ơn bạn đã chia sẻ, hãy nghỉ ngơi nhé! ✨",
        "CalmNote luôn ở đây lắng nghe bạn. 🌿",
        "Bạn đã làm rất tốt hôm nay rồi! 🌟"
    ]
    return render_template('index.html', feedback=random.choice(advices), user=session['username'])

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    entries = Entry.query.filter_by(user_id=session['user_id']).order_by(Entry.date.asc()).all()
    dates = [e.date.strftime("%d/%m") for e in entries][-7:]
    moods = [e.mood for e in entries][-7:]
    return render_template('dashboard.html', entries=entries[::-1], dates=dates, moods=moods)

@app.route('/ai-chat')
def ai_chat():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('chat.html', user=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
