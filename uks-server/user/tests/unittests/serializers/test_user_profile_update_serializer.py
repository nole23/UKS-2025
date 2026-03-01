from django.test import TestCase
from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.auth import get_user_model

from user.serializers import UserProfileUpdateSerializer

User = get_user_model()


# --------------------------
# UserProfileDetailSerializer Tests
# --------------------------
class UserProfileUpdateSerializerTests(TestCase):

    @patch("user.serializers.User.objects")
    def test_update_userprofile_email_taken(self, mock_user_objects):
        # Mokujemo da email ne postoji
        mock_user_objects.exclude.return_value.filter.return_value.exists.return_value = False

        # User i Profile kao jednostavan objekat sa atributima
        user = SimpleNamespace(pk=1, email="test@example.com", first_name="Old", last_name="Old", save=lambda: None)
        profile = SimpleNamespace(user=user, bio="Old bio", save=lambda: None)

        data = {"user": {"email": "newcorp111@example.com"}}

        serializer = UserProfileUpdateSerializer(instance=profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_profile = serializer.save()

        self.assertEqual(updated_profile.user.email, "newcorp111@example.com")

    @patch("user.serializers.User.objects")
    def test_update_userprofile_email_taken(self, mock_user_objects):
        # Mokujemo da email ne postoji
        mock_user_objects.exclude.return_value.filter.return_value.exists.return_value = False

        # User i Profile kao jednostavan objekat sa atributima
        user = SimpleNamespace(pk=1, email="test@example.com", first_name="Old", last_name="Old", save=lambda: None)
        profile = SimpleNamespace(user=user, bio="Old bio", save=lambda: None)

        # Podaci za update
        data = {
            "user": {"first_name": "Testpdated"},
            "bio": "New bio"
        }

        serializer = UserProfileUpdateSerializer(instance=profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_profile = serializer.save()
        # Provere
        self.assertEqual(updated_profile.bio, "New bio")