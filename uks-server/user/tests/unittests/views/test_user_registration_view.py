from django.test import TestCase
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.views import UserRegistrationView

User = get_user_model()


# =========================================================
# Test UserRegistrationView
# =========================================================
class TestUserRegistrationView(TestCase):

    @patch("user.views.Group.objects.get_or_create")
    def test_post_with_roleName(self, mock_get_or_create):
        # --- Mokovana grupa ---
        mock_group_instance = MagicMock()
        mock_get_or_create.return_value = (mock_group_instance, True)

        # --- Mokovani serializer ---
        serializer_mock = MagicMock()
        serializer_mock.is_valid.return_value = True
        user_mock = MagicMock()
        user_mock.username = "testuser"
        user_mock.email = "a@b.com"
        user_mock.groups = MagicMock()
        serializer_mock.save.return_value = user_mock

        view = UserRegistrationView()
        view.get_serializer = MagicMock(return_value=serializer_mock)

        # --- Mokovani request ---
        request_mock = MagicMock()
        request_mock.data = {
            "user": {"username": "testuser", "email": "a@b.com", "password": "pass123!", "password2": "pass123!"},
            "roleName": "Administrator"
        }

        resp = view.post(request_mock)

        # --- Assercije ---
        serializer_mock.is_valid.assert_called_once()
        serializer_mock.save.assert_called_once()
        mock_get_or_create.assert_called_once_with(name="Administrator")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["user"]["username"], "testuser")
    
    @patch("user.views.Group.objects.get_or_create")
    def test_post_without_roleName_default_group(self, mock_get_or_create):
        mock_group_instance = MagicMock()
        mock_get_or_create.return_value = (mock_group_instance, True)

        serializer_mock = MagicMock()
        serializer_mock.is_valid.return_value = True
        user_mock = MagicMock()
        user_mock.username = "testuser2"
        user_mock.email = "b@c.com"
        user_mock.groups = MagicMock()
        serializer_mock.save.return_value = user_mock

        view = UserRegistrationView()
        view.get_serializer = MagicMock(return_value=serializer_mock)

        request_mock = MagicMock()
        request_mock.data = {
            "user": {"username": "testuser2", "email": "b@c.com", "password": "pass123!", "password2": "pass123!"},
            "isSuperadmin": True
        }

        resp = view.post(request_mock)

        serializer_mock.is_valid.assert_called_once()
        serializer_mock.save.assert_called_once()
        mock_get_or_create.assert_called_once_with(name="Superadmin")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["user"]["username"], "testuser2")
