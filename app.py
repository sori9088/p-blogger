import os
from flask import  Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_fontawesome import FontAwesome
import datetime



app = Flask(__name__)
fa = FontAwesome(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
db = SQLAlchemy(app)

class Blog(db.Model) :
    id = db.Column(db.Integer,primary_key = True)
    title = db.Column(db.String(20),nullable=False)
    email = db.Column(db.String(80),nullable=False)
    body = db.Column(db.String,nullable=False)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

class Comment(db.Model) :
    id = db.Column(db.Integer,primary_key = True)
    parent_id = db.Column(db.Integer,nullable=False)
    email = db.Column(db.String(80),nullable=False)
    body = db.Column(db.String,nullable=False)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

class User(db.Model) :
    id = db.Column(db.Integer,primary_key = True)
    email = db.Column(db.String(80),nullable=False)
    pw = db.Column(db.String(10),nullable=False)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())

db.create_all()


@app.route("/", methods=["GET", "POST"])
def new_post():
    if request.method== "POST" :
        new_blog = Blog(title= request.form['title'],
                        email = request.form['email'],
                        body = request.form['body'])
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('new_post'))
    posts = Blog.query.all()
    return render_template("views/index.html", posts=posts)



@app.route("/blogs/<id>", methods=["GET","POST"])
def delete_post(id) :
    if request.method=="POST" :
        post = Blog.query.filter_by(id=id).first() #first() => db에서 첫번째 아이템을 가져온다는 뜻
        if not post:
            return "There is no such post."
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('new_post'))
    return "Not Allowed"


@app.route("/update/<id>", methods=["GET", "POST"])
def update_post(id):
    posts = Blog.query.get(id)
    if request.method == "POST" :
        posts.title = request.form['title']
        posts.body = request.form['body']
        posts.email = request.form['email']
        db.session.commit()
        return redirect(url_for('new_post'))
    return render_template("views/modify.html", posts=posts)


@app.route("/comment/<id>", methods=["GET", "POST"])
def new_comment(id):
    if request.method== "POST" :
        new_comment = Comment(email = request.form['email'],
                              body = request.form['body'],
                              parent_id = id )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('new_post'))
    posts = Blog.query.all()
    return render_template("views/newcomment.html", posts=posts)



@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method== "POST" :
        new_user = User(email = request.form['email'],
                        pw = request.form['password'])
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('new_post'))
    return render_template("views/signin.html")


if __name__ == "__main__":
    app.run(debug=True)