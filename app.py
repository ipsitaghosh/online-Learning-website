from flask import Flask, render_template,request,session,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os
import math
from datetime import datetime

with open('config.json','r') as c:
    params=json.load(c)["params"]
local_server=params['local_server']

app = Flask(__name__)
app.secret_key="super-secret-key"

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-id'],
    MAIL_PASSWORD=params['gmail-password']
)

mail=Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(520), nullable=False)
    date = db.Column(db.String(120), nullable=True)

class Post(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(900000), nullable=False)
    img_file = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(30), nullable=False)
    time_required = db.Column(db.String(20), nullable=False)
    fees=db.Column(db.String(20), nullable=False)
    about = db.Column(db.String(20), nullable=False)


class Login(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(30), nullable=False)
    password=db.Column(db.String(30), nullable=False)
    login_slug=db.Column(db.String(20), nullable=False)
    name=db.Column(db.String(30), nullable=False)
    email=db.Column(db.String(30), nullable=False)

class Courses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    email=db.Column(db.String(30), nullable=False)
    courses=db.Column(db.String(2000), nullable=False)
    slug=db.Column(db.String(30), nullable=False)
    name_slug=db.Column(db.String(30), nullable=False)

@app.route('/')
def index():
    flash("Welcome to Online Learning Website. Happy Learning..","Primary")
    post=Post.query.filter_by().all()
    last = math.ceil(len(post) / int(params['no_of_post']))
    # [0:params['no_of_posts']]
    # pagination
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    post = post[(page - 1) * int(params['no_of_post']): (page - 1) * int(params['no_of_post']) + int(
        params['no_of_post'])]
    # first
    if (page == 1):
        prev = '#'
        next = '/?page=' + str(page + 1)
    elif (page == last):
        prev = '/?page=' + str(page - 1)
        next = '#'
    else:
        prev = '/?page=' + str(page - 1)
        next = '/?page=' + str(page + 1)
    return render_template("index.html",params=params,post=post,prev=prev,next=next)

@app.route('/about')
def about():
    return render_template("about.html",params=params)

@app.route('/post/<string:post_slug>',methods=['GET'])
def post(post_slug):
    post=Post.query.filter_by(slug=post_slug).first()
    return render_template("post.html",params=params,post=post)

@app.route('/contact',methods = ['GET','POST'])
def contact():
    if(request.method=='POST'):
        #add entry to the database

        name=request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        date=datetime.now()

        data=Contact(name=name,email=email,phone_num=phone,message=message,date=date)

        db.session.add(data)
        db.session.commit()

        mail.send_message('New Message From '+name, sender=email, recipients=[params['gmail-id']],
                          body=message+"\n"+phone+"\n"+email)
        flash("Thanks for submitting your details. We will get back to you soon.","success")

    return render_template('contact.html',params=params)

@app.route('/login',methods=['GET','POST'])
def login():
    login = Login.query.all()
    uname_list=[]
    password_list=[]
    login_slug_list=[]
    for l in login:
        uname_list.append(l.uname)
        password_list.append(l.password)
        login_slug_list.append(l.login_slug)

    if ('user' in session and session['user'] in uname_list):
        post = Post.query.all()
        uname=session['user']
        for i in range(len(uname_list)):
            if (uname_list[i] == uname ):
                return redirect('/view/' + login_slug_list[i])
        #return render_template('index.html', params=params, post=post)

    if request.method == 'POST':
        uname = request.form.get('uname')
        password = request.form.get('pass')

        for i in range(len(uname_list)):
            if(uname_list[i]==uname and password==password_list[i]):
                session['user'] = uname  # set the session variable
                post = Post.query.all()
                #return render_template('index.html', params=params, post=post)
                return redirect('/view/'+login_slug_list[i])

    return render_template("login.html",params=params)

@app.route('/register',methods = ['GET','POST'])
def register():
    if(request.method=='POST'):
        #add entry to the database
        name=request.form.get('name')
        uname = request.form.get('uname')
        #slug = request.form.get('login-slug')
        slug=name[:5]+"-post"
        password = request.form.get('password')
        email=request.form.get('email')

        data=Login(name=name,uname=uname,password=password,login_slug=slug,email=email)
        db.session.add(data)
        db.session.commit()

        flash("Thanks for Registration. Your registration is completed. Now go to login to access our course.","success")
    return render_template('register.html',params=params)

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/login')

@app.route('/view/<string:name_slug>',methods=['GET'])
def view(name_slug):
    post = Post.query.all()
    course=Courses.query.filter_by(name_slug=name_slug).all()
    login=Login.query.all()
    return render_template('view.html',params=params,post=post,course=course,login=login,name_slug=name_slug)

@app.route('/add/<string:name_slug>',methods=['GET'])
def add(name_slug):
    post = Post.query.all()
    post_slug_list = []
    course=Courses.query.filter_by(name_slug=name_slug).all()
    course_slug_list=[]
    login=Login.query.all()
    final=[]
    for c in course:
        course_slug_list.append(c.slug)
    for p in post:
        post_slug_list.append(p.slug)
    for p in post_slug_list:
        if p not in course_slug_list:
            final.append(p)
    return render_template('add.html',params=params,post=post,course=course,login=login,final=final,name_slug=name_slug)

@app.route('/addcourse/<string:slug>/<string:name_slug>',methods=['GET'])
def addcourse(slug, name_slug):
    print(name_slug)
    post=Post.query.filter_by(slug=slug).all()
    course=Courses.query.filter_by(name_slug=name_slug).all()
    login=Login.query.filter_by(login_slug=name_slug).all()
    for l in login:
        name=l.name
        email=l.email
    for c in course:
        name_slug=c.name_slug
    for p in post:
        courses=p.title
        slug=p.slug
    data=Courses(name=name,email=email,courses=courses,slug=slug,name_slug=name_slug)
    db.session.add(data)
    db.session.commit()
    return redirect('/view/'+name_slug)

@app.route('/payment/<string:slug>/<string:name_slug>',methods=['GET','POST'])
def payment(slug,name_slug):
    post = Post.query.filter_by(slug=slug).all()
    if (request.method == 'POST'):
        uname=request.form.get('uname')
        post=Post.query.filter_by(slug=slug).all()
    for f in post:
        x=f.fees
    return render_template("payment.html",params=params,x=x,slug=slug,name_slug=name_slug)


app.run(debug=True)