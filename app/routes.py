import logging
from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from app import app, db
from app.models import User

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/entry')
def entry():
    return render_template('entry.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            # Log the received data
            print(f"Received data: username={username}, email={email}")
            logging.info(f"Received data: username={username}, email={email}")

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

            logging.info(f"User {username} added to the database.")

            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logging.error(f"Error during signup: {e}")
            flash('An error occurred while creating your account.', 'error')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')
