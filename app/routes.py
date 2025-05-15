import os
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask import send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import app, db
from app.models import User, Trade, Image, Share
from app.db_tools import can_user_access_image, generate_feed_items, get_ids_from_filename, get_image_filename_from_ids
from datetime import datetime, timedelta
from app.generate_image import create_image
import requests
import os

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_filenames.append(filename)

            new_trade = Trade(user_id=session['user_id'], trade_date=trade_date, profit=float(profit), comment=notes, image_path=','.join(image_filenames) if image_filenames else None)
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

@app.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    #
    # feed_items
    #
    # - type: can be post or image
    # - content: the text that will be displayed in the post
    # - image: the filename of the image, from `static/img/`
    # - author: the name of the author of the post
    #
    feed_items = generate_feed_items(session['user_id'])
    feed_items.reverse()  # order items as newest first
    return render_template('feed.html', feed_items=feed_items)

@app.route('/static/img/<filename>')
def protected_image(filename):
    if 'user_id' not in session:
        flash('You must be logged in to view this image.', 'error')
        return redirect(url_for('login'))

    img_dir = os.path.join(app.root_path, 'static', 'img')
    if not os.path.isfile(os.path.join(img_dir, filename)):
        abort(404)

    author_id, image_id = get_ids_from_filename(filename)
    if can_user_access_image(session['user_id'], image_id):
        return send_from_directory(img_dir, filename)
    return jsonify({'error': 'Not authorised to access this file'}), 403

@app.route('/api/create_image', methods=['POST', 'GET'])
def api_create_image():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in.'}), 401

    try:
        data = request.get_json()
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        share_username = data.get('share')

        # Calculate total profit for the user in the given date range
        start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
        trades = Trade.query.filter(
            Trade.user_id == session['user_id'],
            Trade.trade_date >= start_date,
            Trade.trade_date <= end_date
        ).all()
        amount = sum(trade.profit for trade in trades)

        # Optionally, validate parameters
        if not date_from or not date_to:
            return jsonify({'error': 'Missing required parameters: date_from, date_to.'}), 400

        date_range = f"{date_from} to {date_to}"
        shared_user_id = None
        if share_username:
            shared_user_id = User.query.filter_by(username=share_username).first()
            if not shared_user_id:
                return jsonify({'error': 'User to share with not found.'}), 404

        # Generate a new image entry in the database
        new_image = Image(author_id=session['user_id'])
        db.session.add(new_image)
        db.session.commit()

        # Get filename for the image
        filename = get_image_filename_from_ids(session['user_id'], new_image.image_id)
        img_dir = os.path.join(app.root_path, 'static', 'img')
        os.makedirs(img_dir, exist_ok=True)
        file_path = os.path.join(img_dir, filename)

        create_image(int(amount), date_range, file_path)

        if shared_user_id:
            # add user to shared list
            share_entry = Share(
                share_type="image",
                trade_or_image_id=new_image.image_id,
                user_id_shared_to=shared_user_id.user_id
            )
            db.session.add(share_entry)
            db.session.commit()

        return jsonify({'message': 'Image created successfully.', 'filename': filename}), 201
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({'error': 'Failed to create image.'}), 500

@app.route('/api/user_list', methods=['GET'])
def get_user_list():
    users = User.query.with_entities(User.username).all()
    user_list = {"users": [user[0] for user in users]}
    return user_list

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

@app.route('/api/profits', methods=['GET'])
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
