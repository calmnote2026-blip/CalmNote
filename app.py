from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os, random

app = Flask(__name__)
app.secret_key = "snt_calmnote_ai_v3"
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

# --- HÀM AI PHÂN TÍCH NHẬT KÝ ---
def get_ai_advice(content, mood):
    content = content.lower()
    # Các nhóm từ khóa để AI nhận diện
    stress_keywords = ['mệt', 'áp lực', 'stress', 'nản', 'buồn', 'khóc', 'tệ', 'đau']
    work_keywords = ['học', 'làm', 'deadline', 'công việc', 'thi', 'kiểm tra']
    happy_keywords = ['vui', 'tuyệt', 'hạnh phúc', 'cười', 'xinh', 'đẹp', 'yêu']

    if any(word in content for word in stress_keywords) or mood <= 2:
        return random.choice([
            "Mình cảm nhận được sự mệt mỏi trong lời kể của bạn. Đừng quên rằng sau cơn mưa trời lại sáng, hãy ôm bản thân một cái thật chặt nhé! 🫂",
            "Mọi chuyện khó khăn rồi sẽ qua thôi. Bạn đã rất kiên cường khi đối mặt với nó. Tối nay hãy ngủ thật sớm để lấy lại sức nha. ✨",
            "Đừng quá khắt khe với chính mình. Bạn không cần phải luôn mạnh mẽ. Nghỉ ngơi một chút là để đi xa hơn mà. 🌿"
        ])
    elif any(word in content for word in work_keywords):
        return random.choice([
            "Deadline và học hành có thể làm bạn mỏi mệt, nhưng kết quả ngọt ngào đang đợi phía trước. Cố lên một chút nữa nhé! 🔥",
            "Làm việc chăm chỉ là tốt, nhưng đừng quên uống đủ nước và vận động nhẹ nhàng nha. Bạn làm tốt lắm! ☕",
            "Cứ giải quyết từng việc một, bạn sẽ thấy mình giỏi giang hơn mình tưởng đấy! 🚀"
        ])
    elif any(word in content for word in happy_keywords) or mood >= 4:
        return random.choice([
            "Năng lượng tích cực này thật đáng trân trọng! Hãy lưu giữ khoảnh khắc này để làm động lực cho những ngày tới nhé. ✨",
            "Mình cũng cảm thấy vui lây khi đọc những dòng này của bạn. Cứ tiếp tục tỏa sáng như thế này nha! 🌟",
            "Thật tuyệt vời khi thấy bạn hạnh phúc. Bạn xứng đáng với tất cả những điều tốt đẹp nhất hôm nay! 🎉"
        ])
    else:
        return "Cảm ơn bạn đã tin tưởng chia sẻ với mình. Chúc bạn có một khoảng thời gian thật bình yên và nhẹ lòng. 🌙"

@app.route('/')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', user=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], pin=request.form['pin']).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        flash("Sai thông tin đăng nhập!")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            new_user = User(username=request.form['username'], pin=request.form['pin'])
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except:
            flash("Tên đã tồn tại!")
    return render_template('register.html')

@app.route('/save', methods=['POST'])
def save():
    content = request.form['content']
    mood_val = int(request.form['mood'])
    new_entry = Entry(content=content, mood=mood_val, user_id=session['user_id'])
    db.session.add(new_entry)
    db.session.commit()
    
    # Gọi AI để lấy lời khuyên dựa trên nội dung
    advice = get_ai_advice(content, mood_val)
    return render_template('index.html', feedback=advice, user=session['username'])

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
    return redirect(url_for('logout'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
