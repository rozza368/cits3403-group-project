import os
from dotenv import load_dotenv
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__name__))
default_database_location = 'sqlite:///' + os.path.join(basedir, 'app.db')

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or default_database_location
    SECRET_KEY = os.getenv('SECRET_KEY')