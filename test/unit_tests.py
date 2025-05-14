import unittest

# import stuff from app module

class UnitTests(unittest.TestCase):
    def setUp(self):
        # called immediately before tests
        return super.setUp()

    # create something like what's in __init__

    # ensure we are working on a test database, not the production one!
    # this database should be stored in method

    def tearDown(self):
        return super().tearDown()