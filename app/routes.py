import os
from flask import render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask import send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Trade, Image, Share, Task
from app.blueprints import main
from app.db_tools import can_user_access_image, generate_feed_items, get_ids_from_filename, get_image_filename_from_ids
from datetime import datetime, timedelta
from app.generate_image import create_image
import requests
import os

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

            # Handle image uploads
            image_files = request.files.getlist('images')
            image_filenames = []
            for image in image_files:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    image.save(os.path.join(get_upload_folder(), filename))
                    image_filenames.append(filename)

            if existing_trade:
                # Update the existing trade
                existing_trade.profit = float(profit)
                existing_trade.comment = notes
                if image_filenames:
                    existing_trade.image_path = ','.join(image_filenames)
                else:
                    existing_trade.image_path = None
            else:
                # Create a new trade
                new_trade = Trade(user_id=session['user_id'], trade_date=trade_date, profit=float(profit), comment=notes, image_path=','.join(image_filenames) if image_filenames else None)
                db.session.add(new_trade)
            db.session.commit()

            return jsonify({'message': 'Entry saved successfully!'}), 200
        except Exception as e:
            return jsonify({'error': 'An error occurred while saving the entry.'}), 500

    return render_template('entry.html')

@main.route('/entry/delete', methods=['POST'])
def delete_entry():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    try:
        # Get the date from the request
        data = request.json
        date = data.get('date')

        if not date:
            return jsonify({'error': 'Date is required to delete an entry.'}), 400

        # Parse the date
        trade_date = datetime.strptime(date, '%Y-%m-%d').date()

        # Find the entry for the user and date
        trade = Trade.query.filter_by(user_id=session['user_id'], trade_date=trade_date).first()

        if not trade:
            return jsonify({'error': 'No entry found for the specified date.'}), 404

        # Delete the entry
        db.session.delete(trade)
        db.session.commit()

        return jsonify({'message': 'Entry deleted successfully.'}), 200
    except Exception as e:
        print("Error deleting entry:", e)
        return jsonify({'error': 'An error occurred while deleting the entry.'}), 500

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

@main.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

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

@main.route('/static/img/<filename>')
def protected_image(filename):
    if 'user_id' not in session:
        flash('You must be logged in to view this image.', 'error')
        return redirect(url_for('main.login'))

    img_dir = os.path.join(current_app.root_path, 'static', 'img')
    if not os.path.isfile(os.path.join(img_dir, filename)):
        abort(404)

    author_id, image_id = get_ids_from_filename(filename)
    if can_user_access_image(session['user_id'], image_id):
        return send_from_directory(img_dir, filename)
    return jsonify({'error': 'Not authorised to access this file'}), 403

@main.route('/api/create_image', methods=['POST', 'GET'])
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
        img_dir = os.path.join(current_app.root_path, 'static', 'img')
        os.makedirs(img_dir, exist_ok=True)
        file_path = os.path.join(img_dir, filename)

        create_image(int(amount), date_range, file_path)

        # Only share if the ID is different to that of the user
        if shared_user_id and shared_user_id != session['user_id']:
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
        # Get query parameters
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)

        if not year or not month:
            return jsonify({'error': 'Year and month are required.'}), 400

        # Fetch profits for the specified month
        trades = Trade.query.filter(
            Trade.user_id == session['user_id'],
            db.extract('year', Trade.trade_date) == year,
            db.extract('month', Trade.trade_date) == month
        ).all()

        # Format the data
        profits = [{'day': trade.trade_date.day, 'profit': trade.profit} for trade in trades]

        return jsonify({'month_profits': profits}), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching profits.'}), 500

@main.route('/api/tasks', methods=['GET'])
def get_tasks():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Missing date'}), 400
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    tasks = Task.query.filter_by(user_id=session['user_id'], date=date).all()
    return jsonify([{'id': t.task_id, 'comment': t.comment} for t in tasks])

@main.route('/api/tasks', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    comment = data.get('comment', '').strip()
    date_str = data.get('date')
    if not comment or not date_str:
        return jsonify({'error': 'Missing comment or date'}), 400
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    task = Task(user_id=session['user_id'], comment=comment, date=date)
    db.session.add(task)
    db.session.commit()
    return jsonify({'id': task.task_id, 'comment': task.comment})

@main.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    comment = data.get('comment', '').strip()
    task = Task.query.filter_by(task_id=task_id, user_id=session['user_id']).first_or_404()
    task.comment = comment
    db.session.commit()
    return jsonify({'id': task.task_id, 'comment': task.comment})

@main.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    task = Task.query.filter_by(task_id=task_id, user_id=session['user_id']).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({'result': 'success'})
