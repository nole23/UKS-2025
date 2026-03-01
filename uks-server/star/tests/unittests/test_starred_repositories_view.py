from unittest import TestCase
from unittest.mock import MagicMock, patch
from rest_framework import status
from star.views import StarredRepositoriesView


class StarredRepositoriesViewTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("star.views.Repository.objects")
    @patch("star.views.RepositorySerializer")
    @patch("star.views.cache")
    def test_get_starred_repositories_positive(self, mock_cache, mock_serializer_class, mock_repo_objects):
        mock_repo1 = MagicMock()
        mock_repo2 = MagicMock()
        mock_repo_objects.filter.return_value = [mock_repo1, mock_repo2]

        mock_serializer = MagicMock()
        mock_serializer.data = [{"id": 1}, {"id": 2}]
        mock_serializer_class.return_value = mock_serializer

        request = MagicMock()
        request.user = "user"

        view = StarredRepositoriesView()
        response = view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{"id": 1}, {"id": 2}])
        mock_repo_objects.filter.assert_called_once_with(stars__user="user")
        mock_serializer_class.assert_called_once_with([mock_repo1, mock_repo2], many=True)

    # -------------------
    # GET metoda - negativni slučaj (nema repozitorijuma)
    # -------------------
    @patch("star.views.Repository.objects")
    @patch("star.views.RepositorySerializer")
    @patch("star.views.cache")
    def test_get_starred_repositories_negative_empty(self, mock_cache, mock_serializer_class, mock_repo_objects):
        mock_repo_objects.filter.return_value = []
        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_serializer_class.return_value = mock_serializer

        request = MagicMock()
        request.user = "user"

        view = StarredRepositoriesView()
        response = view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])