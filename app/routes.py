from flask import render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.models import User, Trade
import requests

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
            if not username or not password:
                flash('Username and password are required!', 'error')
                return redirect(url_for('signup'))
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists!', 'error')
                return redirect(url_for('signup'))
            hashed_password = generate_password_hash(password)
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
        if not username or not password:
            flash('Username and password are required!', 'error')
            return redirect(url_for('login'))
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.user_id  # or user.id depending on your model
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('Log out successful.', 'success')
    return redirect(url_for('login'))

@app.route('/api/stats')
def api_stats():
    user_count = User.query.count()
    trade_count = Trade.query.count()
    return jsonify({'users': user_count, 'trades': trade_count})

@app.route('/api/cryptonews')
def api_cryptonews():
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        news = [
            {
                "title": n.get("title"),
                "url": n.get("url"),
                "published_on": n.get("published_on"),
                "source": n.get("source")
            }
            for n in data.get("Data", [])[:6]
        ]
        return jsonify(news)
    except Exception as e:
        print("Crypto news error:", e)
        return jsonify([]), 500

@app.route('/api/cryptoprices')
def api_cryptoprices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,cardano,dogecoin&vs_currencies=usd"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return jsonify(data)
    except Exception as e:
        print("Crypto prices error:", e)
        return jsonify({}), 500
