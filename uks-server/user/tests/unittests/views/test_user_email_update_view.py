from django.test import TestCase
from rest_framework import status
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.views import UserEmailUpdateView

User = get_user_model()


# --------------------------
# UserEmailUpdateView Tests
# --------------------------
class UserEmailUpdateViewTests(TestCase):

    @patch("user.views.UserEmailUpdateSerializer")
    def test_patch_email_positive(self, mock_serializer_class):
        mock_user = MagicMock()
        mock_user.username = "testuser"

        # Kreiramo mock korisnika koji će vratiti .save()
        updated_user = MagicMock()
        updated_user.email = "new@test.com"

        request = MagicMock()
        request.user = mock_user
        request.data = {"old_email": "old@test.com", "new_email": "new@test.com"}

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = updated_user  # <--- važno
        mock_serializer_class.return_value = mock_serializer

        view = UserEmailUpdateView()
        view.request = request
        response = view.patch(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Email updated successfully"})
        mock_serializer.save.assert_called_once()

    @patch("user.views.UserEmailUpdateSerializer")
    def test_patch_email_negative(self, mock_serializer_class):
        mock_user = MagicMock()
        request = MagicMock()
        request.user = mock_user
        request.data = {"old_email": "wrong@test.com", "new_email": "new@test.com"}

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception("Invalid email")
        mock_serializer_class.return_value = mock_serializer

        view = UserEmailUpdateView()
        view.request = request

        with self.assertRaises(Exception):
            view.patch(request)
    
    def test_patch_calls_serializer_save(self):
        view = UserEmailUpdateView()
        request = MagicMock()
        view.request = request

        serializer_mock = MagicMock()
        serializer_mock.is_valid.return_value = True

        with patch("user.views.UserEmailUpdateSerializer", return_value=serializer_mock):
            resp = view.patch(request)
            serializer_mock.save.assert_called_once()
