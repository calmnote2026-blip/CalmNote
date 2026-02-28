from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "snt_calmnote_secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calmnote.db'
db = SQLAlchemy(app)

# Cấu trúc Database cho Người dùng và Nhật ký
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
            return redirect(url_for('login'))
        except:
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
    return render_template('login.html')

@app.route('/save', methods=['POST'])
def save():
    content = request.form['content']
    mood_val = int(request.form['mood'])
    new_entry = Entry(content=content, mood=mood_val, user_id=session['user_id'])
    db.session.add(new_entry)
    db.session.commit()
    
    # Phản hồi AI đơn giản
    feedback = "Cảm ơn bạn đã chia sẻ cùng CalmNote. Hãy nghỉ ngơi nhé! 🌿"
    if mood_val <= 2: feedback = "Mình nhận thấy bạn đang stress. Hãy hít thở sâu, mình luôn ở đây! 💛"
    return render_template('index.html', feedback=feedback, user=session['username'])

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    entries = Entry.query.filter_by(user_id=session['user_id']).order_by(Entry.date.desc()).all()
    return render_template('dashboard.html', entries=entries)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)