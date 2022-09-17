import secrets
import os
from webbrowser import get
from PIL import Image 

from flask import render_template, send_from_directory
from flask import url_for 
from flask import flash 
from flask import redirect
from flask import request, abort
from dss import app, db, bcrypt, mail
from dss.forms import (RegistrationForm,LoginForm, UpdateAccountForm, PostForm,RequestResetForm, ResetPasswordForm) 
from dss.forms import (MaterialsForm) 
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

from apscheduler.schedulers.blocking import BlockingScheduler
from flask_apscheduler import APScheduler
import json
from datetime import datetime
import pandas as pd

from dss.models import (User, MaterialDB, Waste,Technology)
from flask import current_app
from dss.dashboard import getHistoricalData


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

    data = getHistoricalData()

    print(data['trading'])

    return render_template('/base/dashboard.html', data = data)

@app.route("/about")
def about():
    return render_template('/base/about.html', title='About') 

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
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


@app.route("/user/<string:username>") 
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


@app.route("/profile/<user_id>", methods=['GET', 'POST'])
@login_required 
def profile(user_id):

    if request.method == 'POST':
        print(request.form)

        if 'delete_waste_id' in request.form.keys():
            waste_id = request.form['delete_waste_id']
            return redirect(url_for('waste_delete', waste_id = waste_id))

        elif 'delete_tech_id' in request.form.keys():
            tech_id = request.form['delete_tech_id']
            return redirect(url_for('tech_delete', tech_id = tech_id))
        
    user = User.query.filter_by(id=int(user_id)).first()
    waste = Waste.query.filter_by(userId=int(user_id)).all()
    tech = Technology.query.filter_by(userId=int(user_id)).all()
    tech_grouped = Technology.query.filter_by(userId=int(user_id)).group_by(Technology.date)
    
    return  render_template('/base/profile.html', title='My Profile', user = user, waste = waste, tech = tech, tech_grouped = tech_grouped)


@app.route("/waste/<waste_id>")
@login_required 
def waste(waste_id):
    waste = Waste.query.filter_by(id=waste_id).first()

    waste_type = None

    if "{" in waste.type:
        waste_type = json.loads(waste.type.replace("'","\""))
        print(waste_type.keys())

    image_path = []
    if waste.image_path:
    
        image_name = waste.image_path[0:-3].split(";;;")
          
    supplier = User.query.filter_by(id=int(waste.userId)).first()
    
    return  render_template('/base/waste.html', title='Waste information', waste = waste, waste_type = waste_type, supplier = supplier, image_path = image_name)

@app.route("/tech/<tech_id>")
@login_required 
def technology(tech_id):
    tech = Technology.query.filter_by(id=int(tech_id)).first()
    all_tech = Technology.query.filter_by(description = tech.description, date = tech.date).all()

    tech_provider = User.query.filter_by(id=int(tech.userId)).first()

    if tech.product_list:
        product_list = json.loads(tech.product_list.replace("'","\""))

    return  render_template('/base/technology.html', title='Technology information', tech = tech, all_tech =all_tech, tech_provider = tech_provider, product_list = product_list)


@app.route("/newentry/<entry_type>", methods=['GET', 'POST'])
@login_required 
def new_entry(entry_type):
    form = MaterialsForm()
    form.material.choices = [(material.id, material.material) for material in MaterialDB.query.all()]

    wastematerial = [(material.id, material.material) for material in MaterialDB.query.all()]

    if request.method == 'POST':
                
        if entry_type == "waste":
            return redirect(url_for("matching_questions_sellers",materialId=form.material.data))

        elif entry_type == "tech":
            
            materialId = request.form.getlist('tech_waste_id')

            return redirect(url_for("matching_questions_rsp",materialId=materialId))

    return render_template("/base/new_entry.html", entry_type = entry_type, form = form, wastematerial = wastematerial)

@app.route("/waste/<waste_id>/delete")
@login_required 
def waste_delete(waste_id):

    waste = Waste.query.filter_by(id=waste_id).first()

    if waste.lab_report_path:
    
        report_path = os.path.join(app.config["LAB"], waste.lab_report_path)
        os.remove(report_path)

    if waste.image_path:
    
        image_name = waste.image_path[0:-3].split(";;;")

        for img in image_name:
            image_path = os.path.join(app.config["IMAGE"], img)
            os.remove(image_path)
    
    Waste.query.filter_by(id=waste_id).delete()        
    db.session.commit()

    flash('Entry removed','success')
   
    return  redirect(url_for('profile', user_id = current_user.id))

@app.route("/tech/<tech_id>/delete")
@login_required 
def tech_delete(tech_id):
    tech = Technology.query.filter_by(id=tech_id).first()
    all_tech = Technology.query.filter_by(description = tech.description, date = tech.date).delete()
    db.session.commit()
    flash('Entry removed','success')
   
    return  redirect(url_for('profile', user_id = current_user.id))


@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config["LAB"], filename)  

@app.route('/image/<filename>')
def download_image(filename):
    return send_from_directory(app.config["IMAGE"], filename)

@app.route('/save/<filename>')
def save_file(filename):
    os.save(app.config["LAB"], filename) 
    return send_from_directory(app.config["LAB"], filename)      

@app.route('/page',  methods=['GET', 'POST'])
def upload_page():
    return render_template("/base/upload.html") 

@app.route('/upload', methods=['POST'])
def handle_upload():
    for key, f in request.files.items():
        if key.startswith('file'):
            f.save(os.path.join(app.config['LAB'], f.filename))
    return '', 204


@app.route('/form', methods=['POST'])
def handle_form():
    title = request.form.get('title')
    description = request.form.get('description')
    return 'file uploaded and form submit<br>title: %s<br> description: %s' % (title, description)


    return  'file uploaded and form submitted' 