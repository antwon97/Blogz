from flask import request, redirect, render_template, session, flash, url_for

import cgi
from bcrypt import gensalt, hashpw, checkpw
from app import app, db
from models import User, Blog

@app.before_request
def require_login():
    allowed_routes = ['login', 'list_blogs', 'index', 'signup']
    if request.endpoint not in allowed_routes and 'user' not in session:
        return redirect('/login')

def get_blog_owner_ids():
    owner_ids = db.session.query(Blog.owner_id).all()
    owner_ids = [i[0] for i in owner_ids]

    return owner_ids

def get_users():
    users = db.session.query(User).all()

    return users

def get_blog_owner(inId):
    blog_owner = User.query.filter_by(id=inId).first()

    return blog_owner

def get_owner_usernames():

    owner_ids = get_blog_owner_ids()

    owners = []

    for id in owner_ids:
        owners.append(get_blog_owner(id))

    usernames = []

    for owner in owners:
        usernames.append(owner.username)

    return usernames



@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    
    if request.method == 'POST':
        title = request.form['blogTitle']

        content = request.form['blogContent']

        new_blog = Blog(title, content, logged_in_user().id)
        db.session.add(new_blog)
        db.session.commit()

        redir_url = "/blog?id=" + str(new_blog.id)

        return redirect(redir_url)

    return render_template('newpost.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':
        
        inUsername = request.form['username']
        inPwdA = request.form['pworda']
        inPwdB = request.form['pwordb']

        # Flask seems to do validation for input length, and displays related errors
        # The Blogz prompt doesn't seem to talk about not clearing signup input if it's invalid
        # Invalid input is dealt with one field at a time

        if (inUsername.find(' ') != -1):
            flash('Usernames cannot contain spaces')
            return redirect('/signup')

        username_db_count = User.query.filter_by(username=inUsername).count()
        if username_db_count > 0:
            flash(inUsername + 'is already taken, and password reminders are not implemented')
            return redirect('/signup')

        if (inPwdA != inPwdB):
            flash('Passwords did not match')
            return redirect('/signup')
        elif (inPwdA.find(' ') != -1):
            flash('Passwords cannot contain spaces')
            return redirect('/signup')

        salt = gensalt()
        hash = hashpw(inPwdA.encode('utf-8'), salt)

        user = User(username = inUsername, hash = hash)

        db.session.add(user)
        db.session.commit()
        session['user'] = user.username
        return redirect('/newpost')

    else:
        return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['pword']
        
        users = User.query.filter_by(username=username)
        
        if users.count() == 1:
            user = users.first()
            
            if checkpw(password.encode('utf-8'),user.hash.encode('utf-8')):
                session['user'] = user.username
                flash('welcome back, ' + user.username)
                return redirect('/newpost')
            else:
                flash('The username and password combination does not match')
                return redirect('/login')
        else:
            flash(username + ' does not exist')
            return redirect('/login')


@app.route('/logout')
def logout():
    del session['user']
    return redirect('/blog')


@app.route("/blog", methods=['GET'])
def list_blogs():

    userId = request.args.get('user')

    blogId = request.args.get('id')

    if userId is not None:
        # Display only posts from specified user

        userposts = Blog.query.filter_by(owner_id = userId).all()

        curr_user = User.query.filter_by(id=userId).first()

        return render_template('singleUser.html', posts=userposts, user=curr_user)
        
    
    elif blogId is not None:
        #Display only one blog

        blogPosts = []

        blogPosts.append(db.session.query(Blog).get(blogId))

        blog_owner = db.session.query(User).get(blogPosts[0].owner_id)

        username = [blog_owner.username]

        return render_template('blog.html', posts=blogPosts, usernames=username)
        

    else:
        # Display full list

        blogPosts = db.session.query(Blog).all()

        # I know there is something not quite linking up here, but I can't figure out how to solve it.
        # The usernames list being passed to the template seems to be out of order, so the displayed authors are out of order.
        # However, the hrefs seem to properly link to the appropriate blog owner.

        return render_template('blog.html', posts=blogPosts, usernames=get_owner_usernames())

@app.route("/")
def index():

    return render_template('index.html', users=get_users())


def logged_in_user():
    current_user = User.query.filter_by(username=session['user']).first()
    return current_user


app.secret_key = 'AZ9j3XRXH!mJW/7U'

if __name__ == '__main__':
    app.run()