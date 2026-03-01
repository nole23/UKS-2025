from django.test import TestCase
from rest_framework.exceptions import ValidationError
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import override_settings

from user.serializers import UserRegistrationSerializer

User = get_user_model()


# --------------------------
# UserSerializer Tests
# --------------------------
class UserSerializerTests(TestCase):
    
    @patch("user.serializers.Group.objects.get")
    @patch("user.serializers.User.objects.create")
    @override_settings(AUTH_PASSWORD_VALIDATORS=[])
    def test_user_registration_positive(self, mock_user_create, mock_group_get):
        # Mock User instanca
        mock_user = MagicMock()
        mock_user_create.return_value = mock_user

        # Mock Group instanca
        mock_group = MagicMock()
        mock_group_get.return_value = mock_group

        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "S3cure!Pass2026",
            "password2": "S3cure!Pass2026",
            "first_name": "New",
            "last_name": "User"
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # Poziv save() sada koristi mokovan Group
        user = serializer.save()

        # Provere
        mock_user_create.assert_called_once_with(
            username="newuser",
            email="newuser@example.com",
            first_name="New",
            last_name="User"
        )
        mock_user.set_password.assert_called_once_with("S3cure!Pass2026")
        mock_user.save.assert_called_once()
        mock_group_get.assert_called_once_with(name="OrdinaryUser")
        mock_user.groups.add.assert_called_once_with(mock_group)

    def test_user_registration_negative_password_mismatch(self):
        data = {
            "username": "test",
            "email": "test@example.com",
            "password": "Secret123!",
            "password2": "WrongPass!",
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_serializer_password_mismatch_negative(self):
        """Serializer vraća grešku ako se password i password2 ne poklapaju"""
        data = {
            "username": "baduser",
            "email": "baduser@email.com",
            "password": "pass123",
            "password2": "pass456",
            "first_name": "Bad",
            "last_name": "User"
        }
        serializer = UserRegistrationSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("password", context.exception.detail)
