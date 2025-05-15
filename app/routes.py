import os
from flask import render_template, request, redirect, url_for, flash, session, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Trade
from app.blueprints import main
from datetime import datetime, timedelta
import requests

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def get_upload_folder():
    return os.path.join(current_app.root_path, 'static', 'images')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('home.html')

@main.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('index.html')

@main.route('/entry', methods=['GET', 'POST'])
def entry():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        try:
            # Get data from the form
            data = request.form
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

            # Handle image uploads
            image_files = request.files.getlist('images')
            image_filenames = []
            for image in image_files:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    image.save(os.path.join(get_upload_folder(), filename))
                    image_filenames.append(filename)

            new_trade = Trade(user_id=session['user_id'], trade_date=trade_date, profit=float(profit), comment=notes, image_path=','.join(image_filenames) if image_filenames else None)
            db.session.add(new_trade)
            db.session.commit()

            return jsonify({'message': 'Entry saved successfully!'}), 200
        except Exception as e:
            return jsonify({'error': 'An error occurred while saving the entry.'}), 500

    return render_template('entry.html')

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            if not username or not password:
                flash('Username and password are required!', 'error')
                return redirect(url_for('main.signup'))
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists!', 'error')
                return redirect(url_for('main.signup'))
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            flash('An error occurred while creating your account.', 'error')
            return redirect(url_for('main.signup'))
    return render_template('signup.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required!', 'error')
            return redirect(url_for('main.login'))
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.user_id  # or user.id depending on your model
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('main.login'))
    return render_template('login.html')

@main.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('Log out successful.', 'success')
    return redirect(url_for('main.login'))

@main.route('/api/user_list', methods=['GET'])
def get_user_list():
    users = User.query.with_entities(User.username).all()
    user_list = {"users": [user[0] for user in users]}
    return user_list

@main.route('/api/entry', methods=['GET'])
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
            return jsonify({'profit': 0, 'notes': '', 'images': []}), 200

        # Construct full URLs for the images
        image_urls = []
        if trade.image_path:
            image_urls = [url_for('static', filename=f'images/{filename}', _external=True) for filename in trade.image_path.split(',')]

        # Return the entry data
        return jsonify({
            'profit': trade.profit,
            'notes': trade.comment,
            'images': image_urls
        }), 200
    except Exception as e:
        print("Error fetching entry:", e)
        return jsonify({'error': 'An error occurred while fetching the entry.'}), 500

@main.route('/api/stats')
def api_stats():
    user_count = User.query.count()
    trade_count = Trade.query.count()
    return jsonify({'users': user_count, 'trades': trade_count})

@main.route('/api/cryptonews')
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

@main.route('/api/cryptoprices')
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
    
@main.route('/api/profits', methods=['GET'])
def get_profits():
    try:
        # Get the current date
        now = datetime.now()
        year = now.year
        month = now.month
        today = now.day

        # Fetch profits for the current month
        trades = Trade.query.filter(
            Trade.user_id == session['user_id'],
            db.extract('year', Trade.trade_date) == year,
            db.extract('month', Trade.trade_date) == month
        ).all()

        # Format the data
        profits = [{'day': trade.trade_date.day, 'profit': trade.profit} for trade in trades]

        # Fetch profits for the last 7 days
        last_week_start = now - timedelta(days=7)
        last_week_trades = Trade.query.filter(
            Trade.user_id == session['user_id'],
            Trade.trade_date >= last_week_start.date(),
            Trade.trade_date <= now.date()
        ).all()

        last_week_profits = [{'day': trade.trade_date.day, 'profit': trade.profit} for trade in last_week_trades]

        return jsonify({
            'month_profits': profits,
            'last_week_profits': last_week_profits
        }), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching profits.'}), 500
