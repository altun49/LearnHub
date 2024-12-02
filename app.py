import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from flask_sqlalchemy import SQLAlchemy

# Загружаем переменные окружения из .env
load_dotenv()

app = Flask(__name__)

# Указываем секретный ключ для сессий из переменной окружения
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Указываем путь к базе данных из переменной окружения
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

# Инициализация базы данных
db = SQLAlchemy(app)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Модель для курсов
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    video_path = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f"Course('{self.title}', '{self.description}')"


# Модель для пользователей
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)


# Модель для отзывов
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    course = db.relationship('Course', backref=db.backref('reviews', lazy=True))
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))


# Функция для загрузки пользователя
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Главная страница
@app.route('/')
def index():
    courses = Course.query.all()
    return render_template('index.html', courses=courses)


# Страница курса
@app.route('/course/<int:course_id>', methods=['GET', 'POST'])
def course(course_id):
    course = Course.query.get_or_404(course_id)
    reviews = Review.query.filter_by(course_id=course_id).all()

    if request.method == 'POST':
        content = request.form['content']
        user_id = current_user.id if current_user.is_authenticated else 1  # Используем текущего пользователя
        review = Review(content=content, course_id=course.id, user_id=user_id)
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('course', course_id=course.id))

    return render_template('course.html', course=course, reviews=reviews)


# Страница для добавления курса
@app.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        video = request.files['video']
        video_path = os.path.join('static', video.filename)
        video.save(video_path)

        new_course = Course(title=title, description=description, video_path=video_path)
        db.session.add(new_course)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_course.html')


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User()
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')


# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))

    return render_template('login.html')


# Выход из системы
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаем таблицы в базе данных
    app.run(debug=True)
