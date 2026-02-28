from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, random

app = Flask(__name__)
app.secret_key = "snt_calmnote_v4_final"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calmnote.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

def get_ai_advice(content, mood):
    text = content.lower()
    if any(w in text for w in ['mệt', 'buồn', 'tệ', 'áp lực']):
        return "Mình biết bạn đang mệt. Đừng gồng mình quá, hãy nghỉ ngơi một chút nhé. 🫂"
    return "Cảm ơn bạn đã chia sẻ. Chúc bạn một ngày thật bình yên! ✨"

@app.route('/')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    entries = Entry.query.filter_by(user_id=session['user_id']).order_by(Entry.date.desc()).all()
    chart_data = Entry.query.filter_by(user_id=session['user_id']).order_by(Entry.date.asc()).all()
    dates = [e.date.strftime("%d/%m") for e in chart_data][-7:]
    moods = [e.mood for e in chart_data][-7:]
    return render_template('index.html', user=session['username'], entries=entries, dates=dates, moods=moods)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], pin=request.form['pin']).first()
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
            new_user = User(username=request.form['username'], pin=request.form['pin'])
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except: flash("Tên đã tồn tại!")
    return render_template('register.html')

@app.route('/save', methods=['POST'])
def save():
    if 'user_id' not in session: return redirect(url_for('login'))
    new_entry = Entry(content=request.form['content'], mood=int(request.form['mood']), user_id=session['user_id'])
    db.session.add(new_entry)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/ai-chat')
def ai_chat():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('chat.html', user=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
