from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from user.models import User
from user.models import UserProfile

User = get_user_model()


# --------------------------
# Signal za automatsko kreiranje profila
# --------------------------
class UserProfileSignalTests(TestCase):

    def test_profile_signal_positive(self):
        user = User.objects.create_user(username="signaluser", email="signal@example.com", password="pass")
        profile = UserProfile.objects.get(user=user)
        self.assertIsNotNone(profile)

    def test_profile_signal_negative_duplicate(self):
        """
        Negativan test: signal ne dozvoljava dupliranje profila za istog korisnika
        """
        user = User.objects.create_user(username="test", email="test@example.com", password="pass")
        # signal automatski kreira prvi profil
        profile = UserProfile.objects.get(user=user)

        with self.assertRaises(IntegrityError):
            # pokušaj da kreiraš drugi profil za istog korisnika
            UserProfile.objects.create(user=user)
