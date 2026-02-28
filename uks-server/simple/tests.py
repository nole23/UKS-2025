from django.test import TestCase

class SimpleTest(TestCase):
    def test_basic_addition(self):
        self.assertEqual(1 + 1, 2)


from django.test import TestCase
from django.conf import settings

class DatabaseTest(TestCase):
    def test_database_engine(self):
        self.assertIn('sqlite3', settings.DATABASES['default']['ENGINE'])
