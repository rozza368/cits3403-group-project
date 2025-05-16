import unittest
import multiprocessing
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import create_app, db
from app.config import SystemTestConfig
from app.models import User, Trade
from werkzeug.security import generate_password_hash
import time
from datetime import datetime, timedelta

localhost = "http://localhost:5000"

def add_test_user_to_db():
    if not User.query.filter_by(username="testuser").first():
        password = "testpassword3403"
        hashed_password = generate_password_hash(password)
        user = User(username="testuser", email="test@example.com", password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()

def run_flask_app():
    app = create_app(SystemTestConfig)
    with app.app_context():
        db.create_all()
        add_test_user_to_db()
    app.run(port=5000, use_reloader=False)

def get_db_path():
    # Always points to the same test.db as your config
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test.db'))

class SeleniumTests(unittest.TestCase):

    def setUp(self):
        # Runs before each test method
        db_path = get_db_path()
        for _ in range(5):
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
                break
            except PermissionError:
                time.sleep(1)
        self.server_thread = multiprocessing.Process(target=run_flask_app)
        self.server_thread.start()
        time.sleep(2)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(localhost)
        self.login()

    def login(self, username="testuser", password="testpassword3403"):
        self.driver.get(f"{localhost}/login")
        self.driver.find_element("name", "username").send_keys(username)
        self.driver.find_element("name", "password").send_keys(password)
        self.driver.find_element(By.XPATH, "//form//button[contains(text(), 'Sign In')]").click()
        # Wait for the login to complete
        time.sleep(1)

    def tearDown(self):
        # Runs after each test method
        self.server_thread.terminate()
        self.server_thread.join()  # Ensure process is fully stopped
        self.driver.quit()
        db_path = get_db_path()
        for _ in range(5):
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
                break
            except PermissionError:
                time.sleep(1)

    def test_user_exists(self):
        # Connect to the in-memory database to check for the test user
        app = create_app(SystemTestConfig)
        with app.app_context():
            db.create_all()
            add_test_user_to_db()
            user = User.query.filter_by(username="testuser").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, "test@example.com")
            db.session.remove()
            db.engine.dispose()

    def test_create_entry(self):
        # Create a trade entry as testuser
        self.driver.get(f"{localhost}/index")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#calendarGrid .cursor-pointer"))
        )
        day_divs = self.driver.find_elements(By.CSS_SELECTOR, "#calendarGrid .cursor-pointer")
        for div in day_divs:
            if div.text.strip().startswith("1"):
                div.click()
                break
        else:
            raise Exception("Could not find clickable day 1 in calendar.")

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "profitInput"))
        )
        self.driver.find_element(By.ID, "profitInput").click()
        time.sleep(0.25)
        self.driver.find_element(By.ID, "profitInput").clear()
        self.driver.find_element(By.ID, "profitInput").send_keys("100")
        self.driver.find_element(By.ID, "notesInput").clear()
        self.driver.find_element(By.ID, "notesInput").send_keys("Selenium test entry")
        self.driver.find_element(By.ID, "saveBtn").click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/index")
        )

        app = create_app(SystemTestConfig)
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            trade = Trade.query.filter_by(user_id=user.user_id, profit=100, comment="Selenium test entry").first()
            self.assertIsNotNone(trade)
            db.session.remove()
            db.engine.dispose()

    def test_share_trade_and_feed_visibility(self):
        # Create a trade entry as testuser
        self.driver.get(f"{localhost}/index")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#calendarGrid .cursor-pointer"))
        )
        day_divs = self.driver.find_elements(By.CSS_SELECTOR, "#calendarGrid .cursor-pointer")
        for div in day_divs:
            if div.text.strip().startswith("1"):
                div.click()
                break
        else:
            raise Exception("Could not find clickable day 1 in calendar.")

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "profitInput"))
        )
        self.driver.find_element(By.ID, "profitInput").click()
        time.sleep(0.25)
        self.driver.find_element(By.ID, "profitInput").clear()
        self.driver.find_element(By.ID, "profitInput").send_keys("1000")
        self.driver.find_element(By.ID, "notesInput").clear()
        self.driver.find_element(By.ID, "notesInput").send_keys("Selenium share entry")
        self.driver.find_element(By.ID, "saveBtn").click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/index")
        )

        # Share the trade with another user (create the user first)
        app = create_app(SystemTestConfig)
        with app.app_context():
            from app.models import User
            from werkzeug.security import generate_password_hash
            if not User.query.filter_by(username="otheruser").first():
                user = User(username="otheruser", email="other@example.com", password_hash=generate_password_hash("otherpassword"))
                db.session.add(user)
                db.session.commit()
            db.session.remove()
            db.engine.dispose()

        # Open the share profit dialog
        self.driver.get(f"{localhost}")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "shareProfitBtn"))
        )
        self.driver.find_element(By.ID, "shareProfitBtn").click()
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "shareProfitDialog"))
        )
        # Fill out the share form
        today = datetime.today()
        first_of_month = today.replace(day=1)
        first_of_monthstr = first_of_month.strftime("%d-%m-%Y")
        self.driver.find_element(By.ID, "dateFrom").send_keys(first_of_monthstr)
        self.driver.find_element(By.ID, "dateTo").send_keys(first_of_monthstr)
        self.driver.find_element(By.ID, "usernameSearch").send_keys("otheruser")
        self.driver.find_element(By.CSS_SELECTOR, "#shareProfitForm button[type='submit']").click()
        # Wait for confirmation (adjust selector/message as needed)
        WebDriverWait(self.driver, 10).until(
            EC.text_to_be_present_in_element((By.ID, "shareProfitMessage"), "shared")
        )

        # Log out and log in as the other user
        self.driver.get(f"{localhost}/")
        self.driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]").click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        self.driver.find_element(By.NAME, "username").clear()
        self.driver.find_element(By.NAME, "username").send_keys("otheruser")
        self.driver.find_element(By.NAME, "password").clear()
        self.driver.find_element(By.NAME, "password").send_keys("otherpassword")
        self.driver.find_element(By.XPATH, "//form//button[contains(text(), 'Sign In')]").click()
        time.sleep(1)

        # Go to feed and check for the shared trade
        self.driver.get(f"{localhost}/feed")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_source = self.driver.page_source
        self.assertIn("Posted by testuser", page_source)

    def test_previous_month_entry_reflects_on_home(self):
        # Calculate the first day of the previous month
        today = datetime.today()
        first_of_this_month = today.replace(day=1)
        prev_month_last_day = first_of_this_month - timedelta(days=1)
        prev_month_first_day = prev_month_last_day.replace(day=1)
        prev_month_year = prev_month_first_day.year

        # --- Add entry for the current month's 1st day with profit 1000 ---
        self.driver.get(f"{localhost}/index")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "monthYear"))
        )
        # Ensure calendar is on the current month
        while True:
            month_year_text = self.driver.find_element(By.ID, "monthYear").text
            if str(today.year) in month_year_text and today.strftime("%B") in month_year_text:
                break
            self.driver.find_element(By.ID, "nextMonthBtn").click()
            time.sleep(0.25)

        # Click the first day cell for current month
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#calendarGrid .cursor-pointer"))
        )
        day_divs = self.driver.find_elements(By.CSS_SELECTOR, "#calendarGrid .cursor-pointer")
        for div in day_divs:
            if div.text.strip().startswith("1"):
                div.click()
                break
        else:
            raise Exception("Could not find clickable day 1 in calendar (current month).")

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "profitInput"))
        )
        self.driver.find_element(By.ID, "profitInput").click()
        time.sleep(0.25)
        self.driver.find_element(By.ID, "profitInput").clear()
        self.driver.find_element(By.ID, "profitInput").send_keys("1000")
        self.driver.find_element(By.ID, "notesInput").clear()
        self.driver.find_element(By.ID, "notesInput").send_keys("Selenium current month entry")
        self.driver.find_element(By.ID, "saveBtn").click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/index")
        )

        # --- Now add entry for the previous month's 1st day with profit 100 ---
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "monthYear"))
        )
        # Click previous month button until the calendar shows the previous month
        while True:
            month_year_text = self.driver.find_element(By.ID, "monthYear").text
            if str(prev_month_year) in month_year_text and prev_month_first_day.strftime("%B") in month_year_text:
                break
            self.driver.find_element(By.ID, "prevMonthBtn").click()
            time.sleep(0.25)

        # Click the first day cell for previous month
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#calendarGrid .cursor-pointer"))
        )
        day_divs = self.driver.find_elements(By.CSS_SELECTOR, "#calendarGrid .cursor-pointer")
        for div in day_divs:
            if div.text.strip().startswith("1"):
                div.click()
                break
        else:
            raise Exception("Could not find clickable day 1 in calendar (previous month).")

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "profitInput"))
        )
        self.driver.find_element(By.ID, "profitInput").click()
        time.sleep(0.25)
        self.driver.find_element(By.ID, "profitInput").clear()
        self.driver.find_element(By.ID, "profitInput").send_keys("100")
        self.driver.find_element(By.ID, "notesInput").clear()
        self.driver.find_element(By.ID, "notesInput").send_keys("Selenium previous month entry")
        self.driver.find_element(By.ID, "saveBtn").click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/index")
        )

        # --- Go to home page and check the figures ---
        self.driver.get(f"{localhost}/")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "totalEarningsChange"))
        )
        # Check the "+1000% vs same period last month" figure is displayed
        time.sleep(1)
        page_source = self.driver.page_source
        self.assertIn("+900% vs same period last month", page_source)

    def test_create_and_delete_entry(self):
        # Create a trade entry as testuser
        self.driver.get(f"{localhost}/index")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#calendarGrid .cursor-pointer"))
        )
        day_divs = self.driver.find_elements(By.CSS_SELECTOR, "#calendarGrid .cursor-pointer")
        for div in day_divs:
            if div.text.strip().startswith("1"):
                div.click()
                break
        else:
            raise Exception("Could not find clickable day 1 in calendar.")

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "profitInput"))
        )
        self.driver.find_element(By.ID, "profitInput").click()
        time.sleep(0.25)
        self.driver.find_element(By.ID, "profitInput").clear()
        self.driver.find_element(By.ID, "profitInput").send_keys("777")
        self.driver.find_element(By.ID, "notesInput").clear()
        self.driver.find_element(By.ID, "notesInput").send_keys("Delete me test entry")
        self.driver.find_element(By.ID, "saveBtn").click()

        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/index")
        )
        
        # Check in the DB that the trade exists
        app = create_app(SystemTestConfig)
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            trade = Trade.query.filter_by(user_id=user.user_id, profit=777, comment="Delete me test entry").first()
            self.assertIsNotNone(trade)
            db.session.remove()
            db.engine.dispose()

        # Go back to the entry for day 1 and delete it (calendar should still be on current month)
        self.driver.get(f"{localhost}/index")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#calendarGrid .cursor-pointer"))
        )
        day_divs = self.driver.find_elements(By.CSS_SELECTOR, "#calendarGrid .cursor-pointer")
        for div in day_divs:
            if div.text.strip().startswith("1"):
                div.click()
                break
        else:
            raise Exception("Could not find clickable day 1 in calendar.")
        
        time.sleep(0.5)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "deleteEntryBtn"))
        )
        self.driver.find_element(By.ID, "deleteEntryBtn").click()
        WebDriverWait(self.driver, 3).until(EC.alert_is_present())
        alert = self.driver.switch_to.alert
        alert.accept()
        WebDriverWait(self.driver, 10).until(
            EC.url_contains("/index")
        )

        # Check in the DB that the trade is deleted
        app = create_app(SystemTestConfig)
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            trade = Trade.query.filter_by(user_id=user.user_id, profit=777, comment="Delete me test entry").first()
            self.assertIsNone(trade)
            db.session.remove()
            db.engine.dispose()