from unittest.mock import MagicMock, patch
from django.test import TestCase
from rest_framework import status
from repository.views import RepositoryDetailView


# -----------------------------
# RepositoryDetailView
# -----------------------------
class RepositoryDetailViewTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_repository_positive(self, mock_serializer_class, mock_repo_objects):
        # Mock repo koji se vraća iz get
        mock_repo = MagicMock()
        mock_repo_objects.get.return_value = mock_repo

        # Mock serializer
        mock_serializer = MagicMock()
        mock_serializer.data = {"id": 1, "name": "Repo1"}
        mock_serializer_class.return_value = mock_serializer

        # Mock user sa username
        mock_user = MagicMock()
        mock_user.username = "fake_user"

        # Mock request
        request = MagicMock()
        request.user = mock_user  # <- VAŽNO

        view = RepositoryDetailView()
        response = view.get(request, pk=1)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"id": 1, "name": "Repo1"}

    # -------------------
    # DELETE metoda - negativni slučaj (user nije owner)
    # -------------------
    @patch("repository.views.Repository.objects")
    def test_delete_repository_forbidden(self, mock_repo_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "other_user"
        mock_repo_objects.get.return_value = mock_repo

        # mock user
        mock_user = MagicMock()
        mock_user.__eq__.return_value = False  # nije owner

        # groups.filter().exists() -> False
        mock_user.groups.filter.return_value.exists.return_value = False

        request = MagicMock()
        request.user = mock_user

        view = RepositoryDetailView()
        response = view.delete(request, pk=1)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_repo.delete.assert_not_called()

    # -------------------
    # DELETE metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.Repository.objects")
    def test_delete_repository_positive(self, mock_repo_objects):
        mock_repo = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "fake_user"   # <- VAŽNO, ima username
        mock_repo.owner = mock_user
        mock_repo_objects.get.return_value = mock_repo

        request = MagicMock()
        request.user = mock_user  # <- VAŽNO

        view = RepositoryDetailView()
        response = view.delete(request, pk=1)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_repo.delete.assert_called_once()
    
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_repository_cache_hit(self, mock_serializer_class, mock_repo_objects):
        # Mock objekat koji Repository.objects.get ne bi koristio jer cache vraća vrednost
        mock_repo_objects.get.return_value = MagicMock()
        mock_serializer_class.return_value = MagicMock(data={"id": 1})

        # Patch cache.get da vrati "cache hit"
        with patch("repository.views.cache.get", return_value={"id": 99}):
            request = MagicMock()
            mock_user = MagicMock()
            mock_user.username = "user"   # <- VAŽNO
            request.user = mock_user

            view = RepositoryDetailView()
            response = view.get(request, pk=1)

        assert response.data == {"id": 99}

    @patch("repository.views.Repository.objects")
    def test_delete_repository_superadmin(self, mock_repo_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "other_user"
        mock_repo_objects.get.return_value = mock_repo

        mock_user = MagicMock()
        mock_user.groups.filter.return_value.exists.return_value = True
        mock_user.is_superadmin = True

        request = MagicMock()
        request.user = mock_user

        view = RepositoryDetailView()
        response = view.delete(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_repo.delete.assert_called_once()

