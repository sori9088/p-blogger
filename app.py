import os
from flask import  Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_fontawesome import FontAwesome
import datetime
from flask_login import UserMixin , LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
fa = FontAwesome(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'



class Blog(db.Model) :
    id = db.Column(db.Integer,primary_key = True)
    title = db.Column(db.String(20),nullable=False)
    email = db.Column(db.String(80),nullable=False)
    body = db.Column(db.String,nullable=False)
    image_url = db.Column(db.Text,nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

class Comment(db.Model) :
    id = db.Column(db.Integer,primary_key = True)
    parent_id = db.Column(db.Integer,nullable=False)
    email = db.Column(db.String(80),nullable=False)
    body = db.Column(db.String,nullable=False)
    image_url = db.Column(db.Text,nullable=True)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

class User(UserMixin, db.Model) :
    id = db.Column(db.Integer,primary_key = True)
    email = db.Column(db.String(80),nullable=False, unique=True)
    username = db.Column(db.String(80),nullable=False)
    password = db.Column(db.String(10),nullable=False)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def set_password(self, password) :
        self.password = generate_password_hash(password)
    
    def check_password(self,password) :
        return check_password_hash(self.password, password)
    
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated


class Likes(db.Model) :
    id=db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, nullable=False)
    postid=db.Column(db.Integer, nullable=False)
    commentid=db.Column(db.Integer, nullable=True)
    
db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)



@app.route("/", methods=["GET", "POST"])
def view_post():
    posts = Blog.query.all()
    comments = Comment.query.all()
    likes = Likes.query.all()
    for post in posts:
        post.comments = Comment.query.filter_by(parent_id = post.id).all()
        post.likes = Likes.query.filter_by(postid = post.id).all()
    if request.args.get('filter') == 'most-recent':
        posts = Blog.query.order_by(Blog.created.desc()).all()
        return render_template('views/home.html', posts=posts, comments=comments ,likes=likes)
    return render_template("views/home.html", posts=posts, comments=comments, likes=likes)


@app.route("/new_post", methods=["GET", "POST"])
def new_post():
    if request.method== "POST" :
        new_blog = Blog(title= request.form['title'],
                        email = current_user.email,
                        body = request.form['body'],
                        user_id = current_user.id,
                        image_url = request.form['image_url'] )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('view_post'))
    return render_template("views/newpost.html")


@app.route("/posts/<id>", methods=["GET","POST"])
def delete_post(id) :
    if request.method=="POST" :
        post = Blog.query.filter_by(id=id).first() #first() => db에서 첫번째 아이템을 가져온다는 뜻
        if not post:
            return "There is no such post."
        db.session.delete(post)
        Likes.query.filter_by(postid = id).delete()        
        db.session.commit()
        return redirect(url_for('view_post'))
    return "Not Allowed"


@app.route("/update/<id>", methods=["GET", "POST"])
def update_post(id):
    posts = Blog.query.get(id)
    if request.method == "POST" :
        posts.title = request.form['title']
        posts.body = request.form['body']
        posts.image_url = request.form['image_url']
        db.session.commit()
        return redirect(url_for('view_post'))
    return render_template("views/modify.html", posts=posts)


@app.route("/posts/<id>/comments", methods=["GET", "POST"])
def new_comment(id):
    if request.method== "POST" :
        new_comment = Comment(email = current_user.email,
                              body = request.form['body'],
                              image_url = request.form['image_url'],
                              parent_id = id )
        db.session.add(new_comment)
        db.session.commit()
        flash('Thank you for your comment','success')
        return redirect(url_for('view_post', id=id))
    comment = Comment.query.filter_by(parent_id = id).all()
    return render_template("views/newcomment.html",id=id, comments=comment)

@app.route("/posts/comments/<id>", methods=["GET","POST"])
def delete_comment(id) :
    if request.method=="POST" :
        comment = Comment.query.filter_by(id= id).first() #first() => db에서 첫번째 아이템을 가져온다는 뜻
        if not comment:
            return "There is no such comment."
        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for('view_post'))
    return "Not Allowed"

@app.route("/posts/comments/<id>/edit", methods=["GET", "POST"])
def update_comment(id):
    comments = Comment.query.get(id)
    if request.method == "POST" :
        comments.body = request.form['body']
        comments.image_url = request.form['image_url']
        db.session.commit()
        return redirect(url_for('view_post'))
    return render_template("views/comment_modify.html", comments=comments)


@app.route("/signup", methods=["GET", "POST"])

def signup():
    if current_user.is_authenticated :
        return redirect(url_for('view_post'))
    
    if request.method== "POST" :
        user = User.query.filter_by(email = request.form['email']).first()
        if user : 
            flash('Email already taken', 'warning') # we alert the user
            return redirect(url_for('register')) # then reload the register page again

        elif not user :
            user = User(email = request.form['email'], 
                        username= request.form['username'])
            user.set_password(request.form['password'])
            db.session.add(user)
            db.session.commit()
            flash("You've successfully signed up! ", 'success')
            return redirect(url_for('signin'))

        if user.check_password(request.form['password']):
                login_user(user)
                flash('Welcome! {0}'.format(user.email), 'success')
                return redirect(url_for('view_post'))

        flash('Incorrect Password !', 'danger')
        return redirect(url_for('signup'))

    return render_template("views/signup.html")

@app.route("/signin", methods=["GET", "POST"])

def signin():
    if current_user.is_authenticated :
        return redirect(url_for('view_post'))
    
    if request.method== "POST" :
        user = User.query.filter_by(email = request.form['email']).first()

        if not user :
            flash('This account is not registered','warning')
            return redirect(url_for('signup'))

        if user.check_password(request.form['password']):
                login_user(user)
                flash('Welcome! {0}'.format(user.email), 'success')
                return redirect(url_for('view_post'))

        flash('Incorrect Password or Email!', 'danger')
        return redirect(url_for('signin'))

    return render_template("views/signin.html")

@app.route("/signout")
@login_required
def signout():
    logout_user()
    flash("You've successfully signed out!", 'success')
    return redirect(url_for('signin'))

@app.route("/like/<id>" ,methods=["GET", "POST"])
def toggle_like(id):
    if current_user.is_authenticated :
        likes = Likes.query.filter_by(postid=id).filter_by(user_id=current_user.id).first()
        if not likes :
            new_like = Likes(user_id= current_user.id,
                        postid= id)
            db.session.add(new_like)
            db.session.commit() 
            return redirect(url_for('view_post'))
        else :
            db.session.delete(likes)
            db.session.commit()
            return redirect(url_for('view_post'))
    else :
        flash('You have to sign in first','danger')
    return redirect(url_for('view_post'))


if __name__ == "__main__":
    app.run(debug=True)