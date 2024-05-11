from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///socialnetwork.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    birth_date = db.Column(db.DateTime, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(140), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('Like', backref='post', lazy=True)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    per_page = 5

    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('index1.html', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nickname = request.form['nickname']
        email = request.form['email']
        birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d')
        password = request.form['password']
        user = User(nickname=nickname, email=email, birth_date=birth_date, password=password)
        db.session.add(user)
        db.session.commit()
        flash('You have been successfully registered', 'success')
        return redirect(url_for('index'))
    return render_template('register1.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['user_id'] = user.id
            flash('You have been successfully logged in', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    return render_template('login1.html')


@app.route('/make_post', methods=['POST'])
def make_post():
    if 'user_id' not in session:
        flash('You need to login first to make a post', 'danger')
        return redirect(url_for('login'))

    content = request.form['content']
    if len(content) > 140:
        flash('Post cannot exceed 140 characters', 'danger')
        return redirect(url_for('index'))

    user_id = session['user_id']
    post = Post(content=content, user_id=user_id)
    db.session.add(post)

    try:
        db.session.commit()
        flash('Your post has been published!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('An error occurred while publishing your post', 'danger')

    return redirect(url_for('index'))


@app.route('/like/<int:post_id>', methods=['POST'])
def like(post_id):
    if 'user_id' not in session:
        flash('You need to login first to like a post', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Check if the user has already liked the post
    existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()

    if existing_like:
        # If the user has already liked the post, remove the like
        db.session.delete(existing_like)
        db.session.commit()
        flash('You have unliked the post', 'success')
    else:
        # If the user hasn't liked the post yet, add a new like
        new_like = Like(user_id=user_id, post_id=post_id)
        db.session.add(new_like)
        db.session.commit()
        flash('You have liked the post', 'success')

    return redirect(url_for('index'))


@app.route('/user/<int:user_id>')
def user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)
