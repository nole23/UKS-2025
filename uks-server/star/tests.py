from unittest import TestCase
from unittest.mock import MagicMock, patch
from rest_framework import status
from star.views import StarRepositoryView, StarredRepositoriesView


class StarRepositoryViewTests(TestCase):

    # -------------------
    # POST metoda - pozitivni slučaj
    # -------------------
    @patch("star.views.Star.objects")
    @patch("star.views.Repository.objects")
    def test_post_star_positive(self, mock_repo_objects, mock_star_objects):
        mock_repo = MagicMock()
        mock_repo.stars_count = 5
        mock_repo_objects.get.return_value = mock_repo

        mock_star_objects.get_or_create.return_value = (MagicMock(), True)

        request = MagicMock()
        request.user = "fake_user"

        view = StarRepositoryView()
        response = view.post(request, pk=1)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"message": "Starred"}

        mock_star_objects.get_or_create.assert_called_once_with(user="fake_user", repository=mock_repo)
        assert mock_repo.stars_count == 6
        mock_repo.save.assert_called_once()

    # -------------------
    # DELETE metoda - pozitivni slučaj
    # -------------------
    @patch("star.views.Star.objects")
    @patch("star.views.Repository.objects")
    def test_delete_star_positive(self, mock_repo_objects, mock_star_objects):
        mock_repo = MagicMock()
        mock_repo.stars_count = 5
        mock_repo_objects.get.return_value = mock_repo

        mock_star_qs = MagicMock()
        mock_star_objects.filter.return_value = mock_star_qs

        request = MagicMock()
        request.user = "fake_user"

        view = StarRepositoryView()
        response = view.delete(request, pk=1)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"message": "Unstarred"}

        mock_star_objects.filter.assert_called_once_with(user="fake_user", repository=mock_repo)
        mock_star_qs.delete.assert_called_once()
        assert mock_repo.stars_count == 4
        mock_repo.save.assert_called_once()


class StarredRepositoriesViewTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("star.views.Repository.objects")
    @patch("star.views.RepositorySerializer")
    def test_get_starred_repositories_positive(self, mock_serializer_class, mock_repo_objects):
        mock_repo1 = MagicMock()
        mock_repo2 = MagicMock()
        mock_repo_objects.filter.return_value = [mock_repo1, mock_repo2]

        mock_serializer = MagicMock()
        mock_serializer.data = [{"id": 1}, {"id": 2}]
        mock_serializer_class.return_value = mock_serializer

        request = MagicMock()
        request.user = "fake_user"

        view = StarredRepositoriesView()
        response = view.get(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [{"id": 1}, {"id": 2}]

        mock_repo_objects.filter.assert_called_once_with(stars__user="fake_user")
        mock_serializer_class.assert_called_once_with([mock_repo1, mock_repo2], many=True)
