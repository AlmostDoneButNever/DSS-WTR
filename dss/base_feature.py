import secrets
import os
from PIL import Image 

from flask import render_template, send_from_directory
from flask import url_for 
from flask import flash 
from flask import redirect
from flask import request, abort
from dss import app, db, bcrypt, mail
from dss.forms import (RegistrationForm,LoginForm, UpdateAccountForm, PostForm,RequestResetForm, ResetPasswordForm) 
from dss.models import (User, Post)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

from apscheduler.schedulers.blocking import BlockingScheduler
from flask_apscheduler import APScheduler
import json
from datetime import datetime
import pandas as pd

from dss.models import (User, MaterialsDB, WasteDB,TechnologyDB)
from flask import current_app


@app.route("/") 
def home():
    print("this is home")
    return render_template('/base/index.html')

@app.route("/index")
def index():
    return render_template('/base/index.html')

@app.route("/dashboard")
@login_required
def dashboard():
    #posts=db.execute("SELECT * FROM post order by id")
    return render_template('/base/dashboard.html')

@app.route("/about")
def about():
    return render_template('/base/about.html', title='About') 

@app.route("/posts_home")
def posts_home():
    page = request.args.get('page', 1, type=int) 
    posts = Post.query.paginate(page=page, per_page=2) 
    return render_template('/base/posts_home.html', title="Posts Home", posts=posts)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password,listings=0,transacted=0,totalposts=0,totalsuccess=0,totalwaste=0)
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! You are now able to log in", 'success') 
        return redirect(url_for('login'))
    return render_template('/base/register.html', title="Register", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('/base/login.html', title="Login", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(form_picture.filename) 
    picture_fn = random_hex + f_ext 
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn) 
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required 
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
        current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account info has been updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file) 
    return render_template('account.html', title="Account", image_file=image_file, form=form)

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id) 
    return render_template('/base/Post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', 
                            form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('/base/home'))

@app.route("/user/<string:username>") 
def user_posts(username):
    page = request.args.get('page', 1, type=int) 
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=2) 

    return render_template('/base/user_posts.html', posts=posts, user=user) 

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)} 

If you did not make this request, simply ignore this email and no change will be made to your account.
'''
    mail.send(msg)

@app.route("/reset_request", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('/base/reset_request.html', title="Reset Password", form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None: 
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    
    form =  ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash("Your password has been updated! You are now able to log in", 'success') 
        return redirect(url_for('login'))
    return render_template('/base/reset_token.html', title='Reset Password', form=form)


@app.route("/profile/<user_id>")
@login_required 
def profile(user_id):
    user = User.query.filter_by(id=int(user_id)).first()
    waste = WasteDB.query.filter_by(userId=int(user_id)).all()
    tech = TechnologyDB.query.filter_by(userId=int(user_id)).all()

    
    return  render_template('/base/profile.html', title='My Profile', user = user, waste = waste, tech = tech)


@app.route("/waste/<waste_id>")
@login_required 
def waste(waste_id):
    waste = WasteDB.query.filter_by(id=waste_id).first()

    supplier = User.query.filter_by(id=int(waste.userId)).first()

    
    return  render_template('/base/waste.html', title='Waste information', waste = waste, supplier = supplier)

@app.route("/tech/<tech_id>")
@login_required 
def technology(tech_id):
    tech = TechnologyDB.query.filter_by(id=int(tech_id)).first()

    tech_provider = User.query.filter_by(id=int(tech.userId)).first()

    
    return  render_template('/base/technology.html', title='Waste information', tech = tech, tech_provider = tech_provider)


@app.route('/uploads/<filename>')
def download_file(filename):
    path = os.path.join(current_app.root_path, "uploads")
    print(path)
    return send_from_directory(path, filename)