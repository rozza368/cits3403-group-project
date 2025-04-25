from app import db

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(120), nullable=False)

    trades = db.relationship('Trade', backref='user', lazy=True)

class Trade(db.Model):
    __tablename__ = 'trades'
    trade_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    trade_date = db.Column(db.Date, nullable=False)
    profit = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    comment = db.Column(db.String(255), nullable=True)