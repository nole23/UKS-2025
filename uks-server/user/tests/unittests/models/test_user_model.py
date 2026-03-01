from user.models import User
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


# --------------------------
# User Tests
# --------------------------
class UserModelUnitTests(TestCase):

    def test_create_user_positive(self):
        """Pozitivan test: korisnik se kreira ispravno sa validnim podacima"""
        user = User.objects.create_user(username="test", email="test@example.com", password="pass")
        self.assertEqual(str(user), "test")
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.created_at)

    def test_create_user_negative(self):
        """Negativan test: kreiranje korisnika bez username podiže grešku"""
        with self.assertRaises(ValueError):
            User.objects.create_user(username="", email="no_name@example.com", password="pass")
