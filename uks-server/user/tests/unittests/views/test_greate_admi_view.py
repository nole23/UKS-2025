from django.test import TestCase
from unittest.mock import MagicMock, patch
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from user.views import CreateAdminView

User = get_user_model()


# --------------------------
# CreateAdminView Tests
# --------------------------
class CreateAdminViewTest(TestCase):

    def setUp(self):
        self.view = CreateAdminView()
        self.mock_request = MagicMock()
        self.view.request = self.mock_request

    @patch("user.views.User.objects")
    @patch("user.views.Group.objects")
    def test_post_positive(self, mock_group_objects, mock_user_objects):
        """Pozitivan test: kreira admina"""
        self.mock_request.data = {
            "username": "newadmin",
            "email": "admin@email.com",
            "password": "secret123"
        }

        # Mockiranje da username ne postoji
        mock_user_qs = MagicMock()
        mock_user_qs.filter.return_value.exists.return_value = False
        mock_user_objects.return_value = mock_user_objects
        mock_user_objects.filter.return_value = mock_user_qs.filter.return_value

        # Mock User.create_user
        mock_user = MagicMock()
        mock_user_objects.create_user.return_value = mock_user

        # Mock grupa
        mock_group = MagicMock()
        mock_group_objects.get.return_value = mock_group

        response = self.view.post(self.mock_request)

        mock_user_objects.create_user.assert_called_once_with(
            username="newadmin",
            email="admin@email.com",
            password="secret123"
        )
        mock_user.groups.add.assert_called_once_with(mock_group)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.data, {"message": "Admin created"})
        self.assertEqual(response.status_code, 201)

    def test_post_negative_missing_fields(self):
        """Negativan test: fale username ili password"""
        self.mock_request.data = {
            "email": "admin@email.com"
        }

        response = self.view.post(self.mock_request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Missing fields"})

    @patch("user.views.User.objects")
    def test_post_negative_username_exists(self, mock_user_objects):
        """Negativan test: username već postoji"""
        self.mock_request.data = {
            "username": "existinguser",
            "email": "admin@email.com",
            "password": "secret123"
        }

        mock_user_objects.filter.return_value.exists.return_value = True

        response = self.view.post(self.mock_request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Username exists"})
