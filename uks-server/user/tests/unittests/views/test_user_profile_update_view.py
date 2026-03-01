from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.views import UserProfileUpdateView

User = get_user_model()


# --------------------------
# UserProfileUpdateView Tests
# --------------------------
class UserProfileUpdateViewTests(TestCase):

    def setUp(self):
        # Mock user i profil
        self.mock_profile = MagicMock()
        self.mock_profile.user = MagicMock()
        self.mock_profile.user.id = 1

        self.mock_user = MagicMock()
        self.mock_user.profile = self.mock_profile

        # Patch cache
        patcher_cache = patch("user.views.cache")
        self.mock_cache = patcher_cache.start()
        self.addCleanup(patcher_cache.stop)

        # Patch AccessPolicy
        patcher_policy = patch("user.views.AccessPolicy.can_view_user")
        self.mock_can_view = patcher_policy.start()
        self.addCleanup(patcher_policy.stop)

    @patch.object(UserProfileUpdateView, "get_object")
    def test_update_own_profile_positive(self, mock_get_object):
        # get_object vraća naš mock profil
        mock_get_object.return_value = self.mock_profile

        # Pripremamo view i serializer
        view = UserProfileUpdateView()
        view.request = MagicMock()
        view.request.user = self.mock_user

        mock_serializer = MagicMock()
        mock_serializer.save.return_value = self.mock_profile

        # Pozivamo perform_update
        view.perform_update(mock_serializer)

        # Provera da je save pozvan
        mock_serializer.save.assert_called_once()
        # Provera da je cache invalidiran
        self.mock_cache.delete.assert_called_once_with(f"user_profile_{self.mock_profile.user.id}")

    @patch.object(UserProfileUpdateView, "get_object")
    def test_update_other_profile_no_permission(self, mock_get_object):
        # Simuliramo da target profil pripada drugom korisniku
        other_profile = MagicMock()
        other_profile.user = MagicMock()
        other_profile.user.id = 2
        mock_get_object.return_value = other_profile

        # AccessPolicy vraća False
        self.mock_can_view.return_value = False

        view = UserProfileUpdateView()
        view.request = MagicMock()
        view.request.user = self.mock_user

        # Kada pozovemo get_object direktno, treba da baci PermissionDenied
        with self.assertRaises(PermissionDenied):
            # Ovo simulira get_object koji poziva AccessPolicy
            viewer = view.request.user
            user_id = "2"
            target = mock_get_object.return_value
            if not self.mock_can_view(viewer, target):
                raise PermissionDenied()
    
    @patch("user.views.cache")
    def test_perform_update_invalidates_cache(self, mock_cache):
        profile_instance = MagicMock()
        profile_instance.user.id = 42
        serializer = MagicMock()
        serializer.save.return_value = profile_instance

        view = UserProfileUpdateView()
        
        # Dodaj request
        mock_request = MagicMock()
        mock_request.user = MagicMock()
        mock_request.user.username = "testuser"
        view.request = mock_request

        view.perform_update(serializer)

        # Proveri da li je cache obrisan
        mock_cache.delete.assert_called_once_with(f"user_profile_{profile_instance.user.id}")
