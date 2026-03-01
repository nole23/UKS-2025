from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from rest_framework.exceptions import ValidationError
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.views import GenerateUserPasswordView

User = get_user_model()


# --------------------------
# GenerateUserPasswordView Tests
# --------------------------
class GenerateUserPasswordViewTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    # helper — mock permission da uvek dozvoli
    def _view(self):
        return GenerateUserPasswordView.as_view()

    # =====================
    # SUCCESS
    # =====================
    @patch("user.views.IsSuperAdmin.has_permission", return_value=True)
    @patch("user.views.GeneratePasswordSerializer")
    def test_generate_password_success(self, mock_serializer_class, _):

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = "generated123"
        mock_serializer_class.return_value = mock_serializer

        request = self.factory.post("/", {"username": "testuser"}, format="json")
        response = self._view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["password"], "generated123")

    # =====================
    # INVALID SERIALIZER
    # =====================
    @patch("user.views.IsSuperAdmin.has_permission", return_value=True)
    @patch("user.views.GeneratePasswordSerializer")
    def test_generate_password_invalid_serializer(self, mock_serializer_class, _):

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError("Invalid")
        mock_serializer_class.return_value = mock_serializer

        request = self.factory.post("/", {"username": ""}, format="json")
        response = self._view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =====================
    # SAVE ERROR
    # =====================
    @patch("user.views.IsSuperAdmin.has_permission", return_value=True)
    @patch("user.views.GeneratePasswordSerializer")
    def test_generate_password_save_exception(self, mock_serializer_class, _):

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = Exception("DB error")
        mock_serializer_class.return_value = mock_serializer

        request = self.factory.post("/", {"username": "testuser"}, format="json")

        with self.assertRaises(Exception):
            self._view()(request)
        
    @patch("user.views.GeneratePasswordSerializer")
    def test_post_generates_password(self, mock_serializer):
        view = GenerateUserPasswordView()
        request = MagicMock()
        view.request = request

        serializer_instance = mock_serializer.return_value
        serializer_instance.is_valid.return_value = True
        serializer_instance.save.return_value = "NewPass123!"

        resp = view.post(request)
        self.assertEqual(resp.data["password"], "NewPass123!")