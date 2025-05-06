from flask import render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.models import User, Trade
from datetime import datetime
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

@app.route('/entry', methods=['GET', 'POST'])
def entry():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # Get data from the JSON request
            data = request.json
            date = data.get('date')
            profit = data.get('profit')
            notes = data.get('notes', '')

            # Validate data
            if not profit or not date:
                return jsonify({'error': 'Profit and date are required!'}), 400

            # Parse the date
            trade_date = datetime.strptime(date, '%Y-%m-%d').date()

             # Check if a trade already exists for this date and user
            existing_trade = Trade.query.filter_by(user_id=session['user_id'], trade_date=trade_date).first()
            if existing_trade:
                return jsonify({'error': 'A trade already exists for this date!'}), 400

            # Save the entry to the database
            new_trade = Trade(user_id=session['user_id'], trade_date=trade_date, profit=float(profit), comment=notes)
            db.session.add(new_trade)
            db.session.commit()

            return jsonify({'message': 'Entry saved successfully!'}), 200
        except Exception as e:
            return jsonify({'error': 'An error occurred while saving the entry.'}), 500

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

@app.route('/api/entry', methods=['GET'])
def get_entry():
    try:
        # Get query parameters for the date
        day = request.args.get('day')
        month = request.args.get('month')
        year = request.args.get('year')

        # Validate the date
        if not day or not month or not year:
            return jsonify({'error': 'Invalid date parameters.'}), 400

        # Construct the date object
        entry_date = datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d').date()

        # Query the database for the entry
        trade = Trade.query.filter_by(user_id=session['user_id'], trade_date=entry_date).first()

        if not trade:
            return jsonify({'profit': 0, 'notes': ''}), 200

        # Return the entry data
        return jsonify({
            'profit': trade.profit,
            'notes': trade.comment
        }), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching the entry.'}), 500
    
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