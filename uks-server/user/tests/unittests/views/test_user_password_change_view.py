from django.test import TestCase
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.views import UserPasswordChangeView

User = get_user_model()



# --------------------------
# UserPasswordChangeView Tests
# --------------------------
class UserPasswordChangeViewTests(TestCase):

    @patch("user.views.UserPasswordChangeSerializer")
    def test_patch_password_positive(self, mock_serializer_class):
        mock_user = MagicMock()
        request = MagicMock()
        request.user = mock_user
        request.data = {"old_password": "123", "new_password": "456"}

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer

        view = UserPasswordChangeView()
        view.request = request
        response = view.patch(request)

        self.assertEqual(response.data, {"message": "Password changed successfully"})
        mock_serializer.save.assert_called_once()

    @patch("user.views.UserPasswordChangeSerializer")
    def test_patch_password_negative(self, mock_serializer_class):
        mock_user = MagicMock()
        request = MagicMock()
        request.user = mock_user
        request.data = {"old_password": "wrong", "new_password": "456"}

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception("Invalid password")
        mock_serializer_class.return_value = mock_serializer

        view = UserPasswordChangeView()
        view.request = request

        with self.assertRaises(Exception):
            view.patch(request)
