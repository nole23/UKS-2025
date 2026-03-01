from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from unittest.mock import MagicMock, patch
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from user.views import UserProfileDetailView

User = get_user_model()


# --------------------------
# UserProfileDetailView Tests
# --------------------------
class UserProfileDetailViewTests(TestCase):

    def setUp(self):
        # Mock profil i user
        self.mock_profile = MagicMock()
        self.mock_profile.user_id = 1
        self.mock_profile.bio = "User bio"

        self.mock_user = MagicMock()
        self.mock_user.profile = self.mock_profile

        # Patch cache da ne koristi realni cache
        patcher_cache = patch("user.views.cache")
        self.mock_cache = patcher_cache.start()
        self.addCleanup(patcher_cache.stop)

    @patch.object(UserProfileDetailView, "get_object")
    def test_retrieve_own_profile_positive(self, mock_get_object):
        # get_object vraća naš mock profil
        mock_get_object.return_value = self.mock_profile

        # Pripremamo view
        view = UserProfileDetailView()
        view.request = MagicMock()
        view.request.user = self.mock_user
        view.get_serializer = MagicMock(return_value=MagicMock(data={"bio": "User bio"}))

        # Keš nema
        self.mock_cache.get.return_value = None
        self.mock_cache.set.return_value = None

        # Pozivamo retrieve
        response = view.retrieve(view.request)

        # Provera
        self.assertIsInstance(response, Response)
        self.assertEqual(response.data, {"bio": "User bio"})
        self.mock_cache.set.assert_called_once()

    @patch("user.views.get_object_or_404")
    @patch("user.views.AccessPolicy.can_view_user")
    def test_retrieve_other_user_forbidden(self, mock_can_view, mock_get_object):
        # Postavljamo da target user nije dozvoljen za viewer
        mock_target_user = MagicMock()
        mock_target_profile = MagicMock()
        mock_target_profile.user_id = 2
        mock_target_user.profile = mock_target_profile
        mock_get_object.return_value = mock_target_user
        mock_can_view.return_value = False

        view = UserProfileDetailView()
        view.request = MagicMock()
        view.request.user = self.mock_user
        view.request.query_params = {"user_id": 2}

        # Trebalo bi da baci PermissionDenied
        with self.assertRaises(PermissionDenied):
            view.get_object()

    @patch("user.views.get_object_or_404")
    @patch("user.views.AccessPolicy.can_view_user")
    def test_retrieve_other_user_allowed(self, mock_can_view, mock_get_object):
        # Postavljamo da viewer može da vidi target user
        mock_target_user = MagicMock()
        mock_target_profile = MagicMock()
        mock_target_profile.user_id = 2
        mock_target_user.profile = mock_target_profile
        mock_get_object.return_value = mock_target_user
        mock_can_view.return_value = True

        view = UserProfileDetailView()
        view.request = MagicMock()
        view.request.user = self.mock_user
        view.request.query_params = {"user_id": 2}
        view.get_serializer = MagicMock(return_value=MagicMock(data={"bio": "Other bio"}))
        self.mock_cache.get.return_value = None
        self.mock_cache.set.return_value = None

        profile = view.get_object()
        self.assertEqual(profile, mock_target_profile)

        # Testiramo retrieve metod sa keširanjem
        response = view.retrieve(view.request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.data, {"bio": "Other bio"})
        self.mock_cache.set.assert_called_once()

    @patch("user.views.get_object_or_404")
    def test_get_object_permission_denied(self, mock_get):
        user = MagicMock()
        target = MagicMock()
        mock_get.return_value = target
        user.has_perm = False

        view = UserProfileDetailView()
        view.request = MagicMock()
        view.request.user = user
        view.request.query_params = {"user_id": 1}

        # patch AccessPolicy
        with patch("user.views.AccessPolicy.can_view_user", return_value=False):
            with self.assertRaises(PermissionDenied):
                view.get_object()

    @patch("user.views.get_object_or_404")
    @patch("user.views.cache")
    def test_retrieve_caches_profile(self, mock_cache, mock_get):
        profile_mock = MagicMock(user_id=1)
        user = MagicMock()
        user.profile = profile_mock
        view = UserProfileDetailView()
        view.request = MagicMock()
        view.request.user = user
        view.request.query_params = {}

        mock_cache.get.return_value = None

        with patch.object(UserProfileDetailView, "get_serializer", return_value=MagicMock(data={"username": "u1"})):
            resp = view.retrieve(view.request)
            mock_cache.set.assert_called_once()

