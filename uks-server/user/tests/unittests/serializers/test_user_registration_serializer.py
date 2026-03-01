from django.test import TestCase
from user.serializers import UserRegistrationSerializer
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.serializers import UserRegistrationSerializer

User = get_user_model()


# --------------------------
# UserRegistrationSerializer Tests
# --------------------------
class UserRegistrationSerializerTests(TestCase):

    @patch("user.serializers.Group.objects.get")
    @patch("user.serializers.User.objects.create")
    def test_create_user_with_default_group(self, mock_create, mock_get_group):
        mock_user = MagicMock()
        mock_create.return_value = mock_user
        mock_group = MagicMock()
        mock_get_group.return_value = mock_group

        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Pass1234!",
            "password2": "Pass1234!",
            "first_name": "First",
            "last_name": "Last"
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        mock_create.assert_called_once()
        mock_user.set_password.assert_called_once_with("Pass1234!")
        mock_user.groups.add.assert_called_once_with(mock_group)

    def test_password_mismatch(self):
        data = {
            "username": "u",
            "email": "a@a.com",
            "password": "123",
            "password2": "321"
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

