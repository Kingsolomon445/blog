import os
import random
import string
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date

from flask_wtf.csrf import generate_csrf
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
    Bootstrap(app)
    return app


app = create_app()
db = SQLAlchemy(app)
ckeditor = CKEditor(app)
login_manager = LoginManager()
login_manager.init_app(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, ForeignKey('user.id'))
    comments = relationship("Comment")

class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    blog_post_id = db.Column(db.Integer, ForeignKey('blog_posts.id'))

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    blog_post = relationship("BlogPost")

with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(current_user.id)
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    form.csrf_token.data = generate_csrf()
    if request.method == 'POST':
        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data).first():
                flash("You've already signed up with that email, log in instead!")
                return redirect(url_for('login'))
            password = form.password.data
            password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            try:
                user = User(
                    name=form.name.data,
                    email=form.email.data,
                    password=password,
                )
                db.session.add(user)
                db.session.commit()
                login_user(user)
            except Exception as e:
                print(f"{e}")
            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    form.csrf_token.data = generate_csrf()
    if request.method == 'POST':
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("get_all_posts"))
            else:
                flash("Incorrect Password")
        except Exception as e:
            flash(f"This email does not exist!")
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("get_all_posts"))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    form = CommentForm()
    form.csrf_token.data = generate_csrf()
    email = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '@example.com'
    if form.validate_on_submit():
        if current_user.is_authenticated:
            author = current_user.name
            email = current_user.email
        else:
            author = "anonymous"
        comment = Comment(
            author=author,
            body=form.body.data,
            blog_post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
    requested_post = BlogPost.query.get(post_id)
    comments = Comment.query.filter_by(blog_post_id=post_id).all()
    return render_template("post.html", post=requested_post, form=form, comments=comments, email=email)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=['GET', 'POST'])
@admin_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user.name,
            date=date.today().strftime("%B %d, %Y"),
            author_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@admin_required
def edit_post(post_id):
    post = BlogPost.query.filter_by(id=post_id).first()
    form = CreatePostForm(obj=post)
    if request.method == 'POST':
        if form.validate_on_submit():
            form.populate_obj(post)
            db.session.commit()
            flash("Post updated successfully.")
            return redirect(url_for('get_all_posts'))
    return render_template("make-post.html", form=form, type='edit')


@app.route("/delete/<int:post_id>", methods=['GET', 'POST'])
@admin_required
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
