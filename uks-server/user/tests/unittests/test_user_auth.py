from django.test import TestCase
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.serializers import UserRegistrationSerializer
from user.serializers import UserRegistrationSerializer

User = get_user_model()


class UserAuthUnitTests(TestCase):

    # -------------------
    # Registration tests
    # -------------------
    @patch("user.serializers.User.objects.create")
    @patch("user.serializers.Group.objects.get")
    def test_register_user_positive(self, mock_group_get, mock_user_create):
        # Mock User
        mock_user = MagicMock()
        mock_user.username = "newuser"
        mock_user.email = "newuser@email.com"
        mock_user.first_name = "New"
        mock_user.last_name = "User"
        mock_user.set_password = MagicMock()
        mock_user.save = MagicMock()
        mock_user.groups = MagicMock()
        mock_user.groups.add = MagicMock()
        mock_user_create.return_value = mock_user

        # Mock Group
        mock_group = MagicMock()
        mock_group_get.return_value = mock_group

        data = {
            "username": "newuser",
            "email": "newuser@email.com",
            "password": "newpass123",
            "password2": "newpass123",
            "first_name": "New",
            "last_name": "User"
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        mock_user_create.assert_called_once_with(
            username="newuser",
            email="newuser@email.com",
            first_name="New",
            last_name="User"
        )
        mock_user.set_password.assert_called_once_with("newpass123")
        mock_user.save.assert_called_once()
        mock_group_get.assert_called_once_with(name="OrdinaryUser")
        mock_user.groups.add.assert_called_once_with(mock_group)

    def test_register_user_negative_password_mismatch(self):
        data = {
            "username": "baduser",
            "email": "baduser@email.com",
            "password": "pass123",
            "password2": "pass456",
            "first_name": "Bad",
            "last_name": "User"
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)