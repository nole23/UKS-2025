from django.test import TestCase
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.views import UserListAllView

User = get_user_model()


# --------------------------
# UserListAllView Tests
# --------------------------
class UserListAllViewTest(TestCase):
    def setUp(self):
        self.view = UserListAllView()
        self.mock_request = MagicMock()
        self.view.request = self.mock_request
        self.mock_user = MagicMock()
        self.mock_user.pk = 1
        self.mock_request.user = self.mock_user

    @patch("user.views.User.objects")
    def test_get_queryset_positive(self, mock_user_objects):
        """Pozitivan test: vraća queryset sa exclude i prefetch_related"""
        mock_qs = MagicMock()
        mock_exclude_qs = MagicMock()

        # postavimo lanac poziva
        mock_user_objects.prefetch_related.return_value = mock_qs
        mock_qs.exclude.return_value = mock_exclude_qs

        # broj korisnika koji će count vratiti
        mock_exclude_qs.count.return_value = 2

        # mock request user
        self.view.request.user = self.mock_user

        result = self.view.get_queryset()

        # assert da su metode pozvane
        mock_user_objects.prefetch_related.assert_called_once_with("groups")
        mock_qs.exclude.assert_called_once_with(pk=self.mock_user.pk)

        # rezultat je mock exclude queryset
        self.assertEqual(result, mock_exclude_qs)

    @patch("user.views.User.objects")
    def test_get_queryset_negative_empty(self, mock_user_objects):
        """Negativan test: queryset je prazan (npr. nema drugih korisnika)"""
        mock_qs = MagicMock()
        mock_exclude_qs = MagicMock()

        mock_user_objects.prefetch_related.return_value = mock_qs
        mock_qs.exclude.return_value = mock_exclude_qs

        # count treba da vrati 0
        mock_exclude_qs.count.return_value = 0

        # mock request user
        self.view.request.user = self.mock_user

        result = self.view.get_queryset()

        # provera da su metode pozvane
        mock_user_objects.prefetch_related.assert_called_once_with("groups")
        mock_qs.exclude.assert_called_once_with(pk=self.mock_user.pk)

        # rezultat je mock queryset
        self.assertEqual(result, mock_exclude_qs)
