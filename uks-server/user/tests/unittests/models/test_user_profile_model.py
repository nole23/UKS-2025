from django.test import TestCase
from user.models import User
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from user.models import UserProfile, create_user_profile

User = get_user_model()


# --------------------------
# UserProfile Tests
# --------------------------
class UserProfileModelUnitTests(TestCase):

    def setUp(self):
        # Disconnect signal da ne pravi profile automatski
        post_save.disconnect(create_user_profile, sender=User)

    def tearDown(self):
        # Ponovo poveži signal
        post_save.connect(create_user_profile, sender=User)

    def test_create_profile_positive(self):
        user = User.objects.create_user(username="test", email="test@example.com", password="pass")
        profile = UserProfile.objects.create(
            user=user,
            company_name="Test Corp"
        )
        self.assertEqual(profile.user, user)