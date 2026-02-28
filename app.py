from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "snt_calmnote_secret"

# 1. Cấu hình Database (SQLite cho đơn giản và ổn định trên Render)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calmnote.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 2. Cấu trúc Database (Models)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    pin = db.Column(db.String(10), nullable=False)
    entries = db.relationship('Entry', backref='author', lazy=True)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.Integer)  # Mức độ 1-5
    date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# 3. DÒNG QUAN TRỌNG NHẤT: Tự động tạo bảng dữ liệu khi web khởi động
# (Đã đưa ra ngoài khối if __name__ để Render nhận diện được)
with app.app_context():
    db.create_all()

# --- CÁC ĐƯỜNG DẪN (ROUTES) ---

@app.route('/')
def home():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    return render_template('index.html', user=session['username'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            pin = request.form['pin']
            
            # Kiểm tra xem user đã tồn tại chưa
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Tên đăng nhập đã tồn tại!")
                return render_template('register.html')
                
            new_user = User(username=username, pin=pin)
            db.session.add(new_user)
            db.session.commit()
            flash("Đăng ký thành công! Hãy đăng nhập.")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash("Có lỗi xảy ra trong quá trình đăng ký.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], pin=request.form['pin']).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        else:
            flash("Sai tên đăng nhập hoặc mã PIN!")
    return render_template('login.html')

@app.route('/save', methods=['POST'])
def save():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    content = request.form['content']
    mood_val = int(request.form['mood'])
    new_entry = Entry(content=content, mood=mood_val, user_id=session['user_id'])
    db.session.add(new_entry)
    db.session.commit()
    
    # 4. Tích hợp AI Lời khuyên & Phân tích tâm trạng
    feedback = "Cảm ơn bạn đã chia sẻ. Hãy dành thời gian nghỉ ngơi nhé! 🌿"
    if mood_val <= 2: 
        feedback = "CalmNote nhận thấy bạn đang stress nặng. Hít thở sâu và uống một chút nước ấm nhé, mình luôn ở đây! 💛"
    elif mood_val >= 4:
        feedback = "Năng lượng tích cực quá! Hãy lan tỏa niềm vui này đến mọi người nhé! ✨"
        
    return render_template('index.html', feedback=feedback, user=session['username'])

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    # Lấy dữ liệu để làm Bảng thống kê
    entries = Entry.query.filter_by(user_id=session['user_id']).order_by(Entry.date.desc()).all()
    return render_template('dashboard.html', entries=entries)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
