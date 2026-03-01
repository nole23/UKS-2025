from django.test import TestCase
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.views import UserListView

User = get_user_model()


# --------------------------
# UserListView Tests
# --------------------------
class UserListViewTest(TestCase):
    def setUp(self):
        self.mock_user = MagicMock()

    @patch("user.views.AccessPolicy.scope_user_queryset")
    @patch("user.views.User.objects")
    def test_get_queryset_positive_with_query(self, mock_user_objects, mock_scope):
        """Pozitivan test: Admin koristi 'q' parametar za filtriranje username-a"""
        
        # Mock User.objects.all()
        mock_all_qs = MagicMock()
        mock_user_objects.all.return_value = mock_all_qs

        # Mock scope_user_queryset
        scoped_qs = MagicMock()
        mock_scope.return_value = scoped_qs

        # Mock filter vraća drugi MagicMock
        filtered_qs = MagicMock()
        scoped_qs.filter.return_value = filtered_qs

        # Mock .count() na filtered_qs
        filtered_qs.count.return_value = 2

        # Mock request sa query_params
        mock_request = MagicMock()
        mock_request.user = self.mock_user
        mock_request.query_params = {"q": "test"}

        view = UserListView()
        view.request = mock_request

        result = view.get_queryset()

        # Proveri pozive
        mock_user_objects.all.assert_called_once()
        mock_scope.assert_called_once_with(self.mock_user, mock_all_qs)
        scoped_qs.filter.assert_called_once_with(username__icontains="test")

        # Proveri rezultat
        self.assertEqual(result, filtered_qs)

    @patch("user.views.AccessPolicy.scope_user_queryset")
    @patch("user.views.User.objects")
    def test_get_queryset_negative_no_query(self, mock_user_objects, mock_scope):
        """Negativan test: Nema 'q' parametra, vraća ceo scoped queryset"""
        
        # Mock za User.objects.all()
        mock_all_qs = MagicMock()
        mock_user_objects.all.return_value = mock_all_qs

        # Scoped queryset je MagicMock, ne lista
        scoped_qs = MagicMock()
        scoped_qs.count.return_value = 2  # koliko usera vraća
        mock_scope.return_value = scoped_qs

        # Mock request
        mock_request = MagicMock()
        mock_request.user = self.mock_user
        mock_request.query_params = {}  # prazno

        view = UserListView()
        view.request = mock_request

        result = view.get_queryset()

        # Assert pozive
        mock_user_objects.all.assert_called_once()
        mock_scope.assert_called_once_with(self.mock_user, mock_all_qs)
        self.assertEqual(result, scoped_qs)
