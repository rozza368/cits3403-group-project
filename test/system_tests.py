# copy unit_tests.py and modify from there

import unittest
import multiprocessing

# import stuff from app module

class UnitTests(unittest.TestCase):
    def setUp(self):
        # called immediately before tests
        self.server.thread = multiprocessing.Process(target=self.testApplication.run)  # replace with actual application
        self.server.thread.start()

        # add selenium webdriver and options

        return super.setUp()

    # create something like what's in __init__

    # ensure we are working on a test database, not the production one!
    # this database should be stored in method

    def tearDown(self):
        return super().tearDown()