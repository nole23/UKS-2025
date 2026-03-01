from unittest import TestCase
from unittest.mock import MagicMock, patch
from rest_framework import status
from star.views import StarRepositoryView
from repository.models import Repository

class StarRepositoryViewTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("star.views.cache")
    @patch("star.views.Star.objects")
    @patch("star.views.Repository.objects")
    def test_get_starred_users_positive(self, mock_repo_objects, mock_star_objects, mock_cache):
        # Mock korisnik
        mock_user = MagicMock()
        mock_user.is_superadmin = False
        mock_user.is_admin = MagicMock(return_value=False)
        mock_user.id = 1
        mock_user.username = "owner_user"

        # Mock repozitorijum
        mock_repo = MagicMock()
        mock_repo.owner = mock_user
        mock_repo_objects.get.return_value = mock_repo

        # Mock stars
        mock_star = MagicMock()
        mock_star.user.id = 2
        mock_star.user.username = "john"
        mock_star.created_at = "2026-03-01T12:00:00Z"

        mock_star_qs = MagicMock()
        mock_star_qs.select_related.return_value = [mock_star]
        mock_star_objects.filter.return_value = mock_star_qs

        # Mock cache
        mock_cache.get.return_value = None

        # Request
        request = MagicMock()
        request.user = mock_user

        # View
        view = StarRepositoryView()
        response = view.get(request, pk=1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['user_id'], 2)
        self.assertEqual(response.data[0]['user_username'], "john")

    # -------------------
    # GET metoda - negativni slučaj (repo ne postoji)
    # -------------------
    @patch("star.views.Repository.objects")
    def test_get_starred_users_negative_not_found(self, mock_repo_objects):
        # Ispravno side effect za DoesNotExist
        mock_repo_objects.get.side_effect = Repository.DoesNotExist

        request = MagicMock()
        request.user = MagicMock()
        request.user.is_superadmin = True

        view = StarRepositoryView()
        response = view.get(request, pk=999)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"error": "Repository not found"})

    # -------------------
    # POST metoda - pozitivni slučaj
    # -------------------
    @patch("star.views.Star.objects")
    @patch("star.views.Repository.objects")
    @patch("star.views.cache")
    def test_post_star_positive(self, mock_cache, mock_repo_objects, mock_star_objects):
        mock_repo = MagicMock()
        mock_repo.stars_count = 5
        mock_repo_objects.get.return_value = mock_repo
        mock_star_objects.get_or_create.return_value = (MagicMock(), True)

        request = MagicMock()
        request.user = "user"

        view = StarRepositoryView()
        response = view.post(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Starred"})
        self.assertEqual(mock_repo.stars_count, 6)
        mock_repo.save.assert_called_once()

    # -------------------
    # POST metoda - negativni slučaj (repo ne postoji)
    # -------------------
    @patch("star.views.Repository.objects")
    def test_post_star_negative_repo_not_found(self, mock_repo_objects):
        from repository.models import Repository

        mock_repo_objects.get.side_effect = Repository.DoesNotExist
        request = MagicMock()
        request.user = MagicMock()

        view = StarRepositoryView()
        response = view.post(request, pk=999)

        self.assertEqual(response.status_code, 404)

    # -------------------
    # DELETE metoda - pozitivni slučaj
    # -------------------
    @patch("star.views.Star.objects")
    @patch("star.views.Repository.objects")
    @patch("star.views.cache")
    def test_delete_star_positive(self, mock_cache, mock_repo_objects, mock_star_objects):
        mock_repo = MagicMock()
        mock_repo.stars_count = 5
        mock_repo_objects.get.return_value = mock_repo

        mock_star_qs = MagicMock()
        mock_star_objects.filter.return_value = mock_star_qs

        request = MagicMock()
        request.user = "user"

        view = StarRepositoryView()
        response = view.delete(request, pk=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Unstarred"})
        mock_star_qs.delete.assert_called_once()
        self.assertEqual(mock_repo.stars_count, 4)
        mock_repo.save.assert_called_once()

    # -------------------
    # DELETE metoda - negativni slučaj (repo ne postoji)
    # -------------------
    @patch("star.views.Repository.objects")
    def test_delete_star_negative_repo_not_found(self, mock_repo_objects):
        # Ispravno: koristi pravi exception klase modela
        from repository.models import Repository
        mock_repo_objects.get.side_effect = Repository.DoesNotExist

        request = MagicMock()
        request.user = MagicMock()

        view = StarRepositoryView()
        response = view.delete(request, pk=999)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"error": "Repository not found"})