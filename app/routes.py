from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.models import User

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/entry')
def entry():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('entry.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            # Validate form data
            if not username or not password:
                flash('Username and password are required!', 'error')
                return redirect(url_for('signup'))

            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists!', 'error')
                return redirect(url_for('signup'))

            # Hash the password
            hashed_password = generate_password_hash(password)

            # Add user to the database
            new_user = User(username=username, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('An error occurred while creating your account.', 'error')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate form data
        if not username or not password:
            flash('Username and password are required!', 'error')
            return redirect(url_for('login'))

        # Query the database for the user
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.user_id  # Store user ID in session
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
# Clear the session and redirect the user to the login page
def logout():
    session.clear()
    flash('Log out successful.', 'success')
    return redirect(url_for('login'))