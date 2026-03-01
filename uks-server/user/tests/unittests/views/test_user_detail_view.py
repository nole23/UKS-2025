from django.test import TestCase
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.serializers import UserDetailSerializer, UserDetailSuperSerializer
from user.views import UserDetailView

User = get_user_model()

# --------------------------
# UserDetailView Tests
# --------------------------
class UserDetailViewTest(TestCase):
    def setUp(self):
        self.view = UserDetailView()
        self.mock_request = MagicMock()
        self.view.request = self.mock_request
        self.mock_user = MagicMock()
        self.mock_request.user = self.mock_user

    def test_get_serializer_class_superadmin(self):
        """Pozitivan test: ako je user superadmin, vraća UserDetailSuperSerializer"""
        self.mock_user.is_superadmin = True
        serializer_class = self.view.get_serializer_class()
        self.assertEqual(serializer_class, UserDetailSuperSerializer)

    def test_get_serializer_class_regular_user(self):
        """Negativan test: ako nije superadmin, vraća UserDetailSerializer"""
        self.mock_user.is_superadmin = False
        serializer_class = self.view.get_serializer_class()
        self.assertEqual(serializer_class, UserDetailSerializer)

    def test_queryset_methods_called(self):
        # Kreiramo mock za chain metode
        mock_prefetch = MagicMock()
        mock_select = MagicMock()
        mock_select.prefetch_related.return_value = mock_prefetch

        # Patchujemo queryset atribut na view klasi
        with patch.object(UserDetailView, 'queryset', new=MagicMock(select_related=MagicMock(return_value=mock_select))):
            view = UserDetailView()
            # Pozivamo chain
            qs = view.queryset.select_related("profile").prefetch_related("groups")

            # Provere
            view.queryset.select_related.assert_called_once_with("profile")
            mock_select.prefetch_related.assert_called_once_with("groups")
            self.assertEqual(qs, mock_prefetch)
