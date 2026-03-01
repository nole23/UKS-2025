from django.test import TestCase
from rest_framework.test import APIRequestFactory
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.views import PersonalTokenListView

User = get_user_model()


# --------------------------
# PersonalTokenListView Tests
# --------------------------
class PersonalTokenListViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.mock_user = MagicMock()

    @patch("user.views.PersonalToken.objects")
    def test_get_queryset_returns_tokens_for_user(self, mock_objects):
        # Mock filter vraća objekt sa .count()
        mock_qs = MagicMock()
        mock_qs.count.return_value = 2  # broj tokena
        mock_objects.filter.return_value = mock_qs

        # Kreiramo request i view
        request = self.factory.get("/fake-url/")
        request.user = self.mock_user

        view = PersonalTokenListView()
        view.request = request

        result = view.get_queryset()

        # Provera da se filter pozvao sa pravim korisnikom
        mock_objects.filter.assert_called_once_with(user=self.mock_user)
        # Rezultat je isti mock
        self.assertEqual(result, mock_qs)
        # Provera da je count pozvan
        mock_qs.count.assert_called_once()
