from django.test import TestCase
from rest_framework.exceptions import ValidationError
from unittest.mock import MagicMock
from django.contrib.auth import get_user_model

from user.views import PersonalTokenCreateView

User = get_user_model()


# --------------------------
# PersonalTokenCreateView Tests
# --------------------------
class PersonalTokenCreateViewTests(TestCase):

    def setUp(self):
        # Mock user i personal_tokens
        self.mock_user = MagicMock()
        self.mock_user.personal_tokens.count.return_value = 0  # default

    def test_create_personal_token_positive(self):
        # User ima manje od 5 tokena
        self.mock_user.personal_tokens.count.return_value = 3

        view = PersonalTokenCreateView()
        view.request = MagicMock()
        view.request.user = self.mock_user

        mock_serializer = MagicMock()
        view.perform_create(mock_serializer)

        # Proveravamo da je serializer.save pozvan sa user
        mock_serializer.save.assert_called_once_with(user=self.mock_user)

    def test_create_personal_token_limit_reached(self):
        # User ima 5 tokena → greška
        self.mock_user.personal_tokens.count.return_value = 5

        view = PersonalTokenCreateView()
        view.request = MagicMock()
        view.request.user = self.mock_user

        mock_serializer = MagicMock()

        with self.assertRaises(ValidationError) as context:
            view.perform_create(mock_serializer)

        self.assertEqual(str(context.exception.detail[0]), "Token limit reached")
        # Proveravamo da save NIJE pozvan
        mock_serializer.save.assert_not_called()
    
    def test_perform_create_token_limit(self):
        user = MagicMock()
        user.personal_tokens.count.return_value = 5
        view = PersonalTokenCreateView()
        view.request = MagicMock()
        view.request.user = user
        serializer = MagicMock()

        with self.assertRaises(ValidationError):
            view.perform_create(serializer)

    def test_perform_create_saves_user(self):
        user = MagicMock()
        user.personal_tokens.count.return_value = 0
        view = PersonalTokenCreateView()
        view.request = MagicMock()
        view.request.user = user
        serializer = MagicMock()
        view.perform_create(serializer)
        serializer.save.assert_called_once_with(user=user)
