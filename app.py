import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import time
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_babel import Babel

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    video_path = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f"Course('{self.title}', '{self.description}')"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    course = db.relationship('Course', backref=db.backref('reviews', lazy=True))
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    courses = Course.query.all()
    return render_template('index.html', courses=courses)


@app.route('/course/<int:course_id>')
def course(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('course.html', course=course)


@app.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        video = request.files['video']
        video_path = os.path.join('static', f"{int(time.time())}_{video.filename}")
        video.save(video_path)

        new_course = Course(title=title, description=description, video_path=video_path)
        db.session.add(new_course)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_course.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        user = User(username=username, password=password_hash)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# Новый маршрут для профиля
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


# Новый маршрут для страницы преподавателей
@app.route('/teachers')
def teachers():
    return render_template('teachers.html')


# Новый маршрут для страницы студентов
@app.route('/students')
def students():
    return render_template('students.html')


# Новый маршрут для курсов (показывает все курсы)
@app.route('/courses')
def courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)


# Админка
admin = Admin(app, name='Admin Dashboard', template_mode='bootstrap3')
admin.add_view(ModelView(Course, db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Review, db.session))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаем таблицы в базе данных
    app.run(debug=True)
