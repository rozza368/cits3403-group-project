import unittest
from app import create_app, db
from app.models import User, Trade, Image, Share
from app.config import TestConfig
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

def add_test_user_to_db():
    # Define a test user and add it to the database
    password = "testpassword"
    hashed_password = generate_password_hash(password)
    user = User(username="testuser", email="test@example.com", password_hash=hashed_password)
    db.session.add(user)
    db.session.commit()

class BasicTests(unittest.TestCase):
    
    def setUp(self):
        # Runs before each test method
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # Add test data to the database
        add_test_user_to_db()

    def tearDown(self):
        # Runs after each test method
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_user(self):
        # Create User
        password = "create_user_test"
        hashed_password = generate_password_hash(password)
        user = User(username="createtest", email="create@example.com", password_hash=hashed_password)

        # Add user to the session and commit
        db.session.add(user)
        db.session.commit()

        # Query and check if the user was created successfully
        queried_user = User.query.filter_by(username="createtest").first()
        self.assertIsNotNone(queried_user)
        self.assertEqual(queried_user.email, "create@example.com")
        self.assertNotEqual(queried_user.email, "wrong@example.com")
        self.assertTrue(check_password_hash(queried_user.password_hash, password))
        self.assertFalse(check_password_hash(queried_user.password_hash, "wrongpassword"))

    def test_create_and_edit_entry(self):
        # Use the test user created by add_test_user_to_db
        user = User.query.filter_by(username="testuser").first()

        # Create a trade entry for the user
        trade = Trade(user_id=user.user_id, trade_date=date(2024, 5, 17), profit=3403, comment="Initial entry")
        db.session.add(trade)
        db.session.commit()

        # Query and check the entry
        queried_trade = Trade.query.filter_by(user_id=user.user_id, trade_date=date(2024, 5, 17)).first()
        self.assertIsNotNone(queried_trade)
        self.assertEqual(queried_trade.profit, 3403)
        self.assertEqual(queried_trade.comment, "Initial entry")

        # Edit the entry
        queried_trade.profit = 200
        queried_trade.comment = "Edited entry"
        db.session.commit()

        # Query and check the updated entry
        updated_trade = Trade.query.filter_by(user_id=user.user_id, trade_date=date(2024, 5, 17)).first()
        self.assertEqual(updated_trade.profit, 200)
        self.assertEqual(updated_trade.comment, "Edited entry")

    def test_share_image_access(self):
        # Create three users: author, recipient and one extra user who does not have access
        author = User(username="author", email="author@example.com", password_hash=generate_password_hash("pass"))
        recipient = User(username="recipient", email="recipient@example.com", password_hash=generate_password_hash("pass"))
        other = User(username="other", email="other@example.com", password_hash=generate_password_hash("pass"))
        db.session.add_all([author, recipient, other])
        db.session.commit()

        # Create an image by the author
        image = Image(author_id=author.user_id)
        db.session.add(image)
        db.session.commit()

        # Share the image with the recipient
        share = Share(share_type="image", trade_or_image_id=image.image_id, user_id_shared_to=recipient.user_id)
        db.session.add(share)
        db.session.commit()

        # Simulate the can_user_access_image function (import if available)
        from app.db_tools import can_user_access_image

        # Author should have access
        self.assertTrue(can_user_access_image(author.user_id, image.image_id))
        # Recipient should have access
        self.assertTrue(can_user_access_image(recipient.user_id, image.image_id))
        # A random user should not have access
        self.assertFalse(can_user_access_image(other.user_id, image.image_id))

    def test_duplicate_user(self):
        # Attempt to create a duplicate user
        with self.assertRaises(Exception):
            add_test_user_to_db()

    def test_monthly_profits_total_and_edit(self):
        # Use the test user created by add_test_user_to_db
        user = User.query.filter_by(username="testuser").first()

        # Create multiple trade entries for May 2024
        trades = [
            Trade(user_id=user.user_id, trade_date=date(2024, 5, 1), profit=100, comment="Entry 1"),
            Trade(user_id=user.user_id, trade_date=date(2024, 5, 10), profit=200, comment="Entry 2"),
            Trade(user_id=user.user_id, trade_date=date(2024, 5, 20), profit=300, comment="Entry 3"),
        ]
        db.session.add_all(trades)
        db.session.commit()

        # Simulate login for the test client
        test_client = self.app.test_client()
        with test_client.session_transaction() as sess:
            sess['user_id'] = user.user_id

        # Call the /api/profits endpoint for May 2024
        response = test_client.get('/api/profits?year=2024&month=5')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        month_profits = data['month_profits']
        total = sum(entry['profit'] for entry in month_profits)
        self.assertEqual(total, 600)

        # Edit one of the entries
        trade_to_edit = Trade.query.filter_by(user_id=user.user_id, trade_date=date(2024, 5, 10)).first()
        trade_to_edit.profit = 500
        db.session.commit()

        # Call the /api/profits endpoint again
        response = test_client.get('/api/profits?year=2024&month=5')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        month_profits = data['month_profits']
        total = sum(entry['profit'] for entry in month_profits)
        self.assertEqual(total, 900)
        self.assertNotEqual(total, 600)

    def test_entry_errors(self):
        test_client = self.app.test_client()
        user = User.query.filter_by(username="testuser").first()
        with test_client.session_transaction() as sess:
            sess['user_id'] = user.user_id

        # Missing profit
        response = test_client.post('/entry', data={'date': '2024-05-17'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

        # Missing date
        response = test_client.post('/entry', data={'profit': 100})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

        # Invalid date format
        response = test_client.post('/entry', data={'date': 'invalid-date', 'profit': 100})
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.get_json())