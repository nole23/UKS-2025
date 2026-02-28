from unittest.mock import MagicMock, patch
from django.test import TestCase
from repository.views import RepositoryBadgeUpdateView
from repository.models import Repository


# -----------------------------
# RepositoryBadgeUpdateView unit tests
# -----------------------------
class RepositoryBadgeUpdateViewTests(TestCase):

    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_patch_badge_owner(self, mock_serializer_class, mock_repo_objects):
        mock_user = MagicMock()
        mock_user.is_superadmin = False

        # owner mora biti isti objekat kao user
        mock_repo = MagicMock()
        mock_repo.owner = mock_user
        mock_repo.badge = "NONE"
        mock_repo_objects.get.return_value = mock_repo

        request = MagicMock()
        request.user = mock_user
        request.data = {"badge": "VERIFIED"}

        view = RepositoryBadgeUpdateView()
        response = view.patch(request, pk=1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_repo.badge, "VERIFIED")
        mock_serializer_class.assert_called_once_with(mock_repo)

    @patch("repository.views.Repository.objects")
    def test_patch_badge_forbidden(self, mock_repo_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "other_user"
        mock_repo.badge = "NONE"
        mock_repo_objects.get.return_value = mock_repo

        mock_user = MagicMock()
        mock_user.is_superadmin = False

        request = MagicMock()
        request.user = mock_user
        request.data = {"badge": "OFFICIAL"}

        view = RepositoryBadgeUpdateView()
        response = view.patch(request, pk=1)
        self.assertEqual(response.status_code, 403)

    @patch("repository.views.Repository.objects")
    def test_patch_badge_invalid_value(self, mock_repo_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "owner"
        mock_repo.badge = "NONE"
        mock_repo_objects.get.return_value = mock_repo

        mock_user = MagicMock()
        mock_user.is_superadmin = True

        request = MagicMock()
        request.user = mock_user
        request.data = {"badge": "INVALID_BADGE"}

        view = RepositoryBadgeUpdateView()
        response = view.patch(request, pk=1)
        self.assertEqual(response.status_code, 400)

    @patch("repository.views.Repository.objects")
    def test_patch_badge_repo_not_found(self, mock_repo_objects):
        # koristi pravi DoesNotExist exception
        mock_repo_objects.get.side_effect = Repository.DoesNotExist

        mock_user = MagicMock()
        mock_user.is_superadmin = True

        request = MagicMock()
        request.user = mock_user
        request.data = {"badge": "OFFICIAL"}

        view = RepositoryBadgeUpdateView()
        response = view.patch(request, pk=1)
        
        # view treba da uhvati DoesNotExist i vrati 404
        self.assertEqual(response.status_code, 404)