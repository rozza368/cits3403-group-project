from app import db

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    trades = db.relationship('Trade', backref='user', lazy=True)

class Trade(db.Model):
    __tablename__ = 'trades'
    trade_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    trade_date = db.Column(db.Date, nullable=False)
    profit = db.Column(db.Integer, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    comment = db.Column(db.String(255), nullable=True)

    # Composite unique constraint for user_id and trade_date
    __table_args__ = (
        db.UniqueConstraint('user_id', 'trade_date', name='unique_user_trade_date'),
    )

class Image(db.Model):
    __tablename__ = 'images'
    image_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

class Share(db.Model):
    __tablename__ = 'shares'
    # either 'post' or 'image'
    share_type = db.Column(db.String(10), primary_key=True)
    # refers to either trades.trade_id or images.image_id depending on share_type.
    trade_or_image_id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id_shared_to = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True, nullable=False)

class Task(db.Model):
    __tablename__ = 'tasks'
    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    comment = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=False, unique=True)