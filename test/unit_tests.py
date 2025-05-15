import unittest
from app import create_app, db
from app.models import User
from app.config import TestConfig
from werkzeug.security import generate_password_hash, check_password_hash

class BasicTests(unittest.TestCase):
    
    def setUp(self):
        # Runs before each test method
        testapp = create_app(TestConfig)
        self.app_context = testapp.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        # Runs after each test method
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_user(self):
        # Test user creation
        password = "testpassword"
        hashed_password = generate_password_hash(password)
        user = User(username="testuser", email="test@example.com", password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        queried_user = User.query.filter_by(username="testuser").first()
        self.assertIsNotNone(queried_user)
        self.assertEqual(queried_user.email, "test@example.com")
        self.assertNotEqual(queried_user.email, "wrong@example.com")
        self.assertTrue(check_password_hash(queried_user.password_hash, password))
        self.assertFalse(check_password_hash(queried_user.password_hash, "wrongpassword"))