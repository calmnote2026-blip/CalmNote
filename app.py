from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, random

app = Flask(__name__)
app.secret_key = "snt_calmnote_secret_2026_smooth"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calmnote.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Cấu trúc Database (Models) ---
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

# Tự động tạo bảng dữ liệu khi web khởi động
with app.app_context():
    db.create_all()

# --- CÁC ĐƯỜNG DẪN (ROUTES) ---
@app.route('/')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', user=session['username'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # SNT check tên tồn tại
            existing_user = User.query.filter_by(username=request.form['username']).first()
            if existing_user:
                flash("Tên đăng nhập đã tồn tại!")
                return render_template('register.html')
                
            new_user = User(username=request.form['username'], pin=request.form['pin'])
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash("Có lỗi xảy ra.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], pin=request.form['pin']).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        flash("Sai thông tin đăng nhập hoặc mã PIN!")
    return render_template('login.html')

@app.route('/save', methods=['POST'])
def save():
    mood_val = int(request.form['mood'])
    new_entry = Entry(content=request.form['content'], mood=mood_val, user_id=session['user_id'])
    db.session.add(new_entry)
    db.session.commit()
    
    # Đa dạng hóa lời phản hồi AI cho SNT
    advices = {
        1: [
            "Mình thấy bạn đang rất mệt mỏi. Đừng gồng mình quá, hãy nghỉ ngơi nhé! 🫂",
            "Mọi chuyện buồn rồi sẽ qua thôi. Hãy cho phép mình nghỉ một chút. 💛",
            "Đừng quên hít thở sâu, bạn đã cố gắng rất nhiều rồi. 🌟"
        ],
        2: [
            "Hôm nay có vẻ hơi khó khăn. Mình luôn ở đây lắng nghe bạn. 🌿",
            "Hãy tìm một chút niềm vui nhỏ để xoa dịu tâm hồn nhé. 😊",
            "Nụ cười của bạn là điều đẹp nhất hôm nay. Đừng để nó tắt nhé! 😊"
        ],
        3: [
            "Một ngày bình yên cũng là một điều đáng quý. ☕",
            "Hãy tận hưởng sự tĩnh lặng này và sạc lại năng lượng. 🔋",
            "Bạn đang làm rất tốt, cứ duy trì như vậy nhé! ✨"
        ],
        4: [
            "Tuyệt vời! Hãy lan tỏa năng lượng tích cực này nhé! ✨",
            "Chúc mừng bạn đã có một ngày thật ý nghĩa. 🎉",
            "Niềm vui của bạn cũng là niềm vui của mình. Cảm ơn bạn! 😊"
        ],
        5: [
            "Bạn đang tỏa sáng rực rỡ! Hãy giữ vững phong độ này nhé. 🎉",
            "Một ngày hoàn hảo! Mình chúc mừng bạn rực rỡ. ✨",
            "Hạnh phúc đang mỉm cười với bạn, hãy tận hưởng nó! 🌟"
        ]
    }
    return render_template('index.html', feedback=random.choice(advices.get(mood_val)), user=session['username'])

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    # Lấy nhật ký và sắp xếp theo ngày tăng dần cho biểu đồ SNT
    entries = Entry.query.filter_by(user_id=session['user_id']).order_by(Entry.date.asc()).all()
    # Chuẩn bị dữ liệu cho biểu đồ 
    dates = [e.date.strftime("%d/%m") for e in entries][-7:] # Lấy 7 ngày gần nhất
    moods = [e.mood for e in entries][-7:]
    # Trả nhật ký theo thứ tự mới nhất để hiển thị SNT
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
