from unittest import TestCase
from unittest.mock import MagicMock, patch
from rest_framework import status
from .views import RepositoryTagListView  # prilagodi putanju
from repository.models import Repository


class RepositoryTagListViewTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("tag.views.Tag.objects")
    def test_get_tags_positive(self, mock_tag_objects):
        # Kreiramo mock tagove
        tag1 = MagicMock()
        tag1.id = 1
        tag1.name = "latest"
        tag1.digest = "sha256:abcd"
        tag1.compressed_size_mb = 150
        tag1.os_arch = "linux/amd64"
        tag1.created_at = "2026-01-27T00:00:00Z"
        tag1.updated_at = "2026-01-27T01:00:00Z"

        tag2 = MagicMock()
        tag2.id = 2
        tag2.name = "v1.0"
        tag2.digest = "sha256:efgh"
        tag2.compressed_size_mb = 145
        tag2.os_arch = "linux/arm64"
        tag2.created_at = "2026-01-27T00:30:00Z"
        tag2.updated_at = "2026-01-27T01:30:00Z"

        # Mock order_by da vrati listu tagova
        mock_filter = MagicMock()
        mock_filter.order_by.return_value = [tag1, tag2]
        mock_tag_objects.filter.return_value = mock_filter

        request = MagicMock()
        request.user = "fake_user"

        view = RepositoryTagListView()
        response = view.get(request, pk=1)

        # Očekivani podaci
        expected_data = [
            {
                "id": 1,
                "name": "latest",
                "digest": "sha256:abcd",
                "compressed_size_mb": 150,
                "os_arch": "linux/amd64",
                "created_at": "2026-01-27T00:00:00Z",
                "updated_at": "2026-01-27T01:00:00Z"
            },
            {
                "id": 2,
                "name": "v1.0",
                "digest": "sha256:efgh",
                "compressed_size_mb": 145,
                "os_arch": "linux/arm64",
                "created_at": "2026-01-27T00:30:00Z",
                "updated_at": "2026-01-27T01:30:00Z"
            }
        ]

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected_data
        mock_tag_objects.filter.assert_called_once_with(repository_id=1)

    # -------------------
    # POST metoda - pozitivni slučaj
    # -------------------
    @patch("tag.views.Tag.objects")
    @patch("tag.views.Repository.objects")
    def test_post_tag_positive(self, mock_repo_objects, mock_tag_objects):
        mock_repo = MagicMock()
        mock_repo.id = 1
        mock_repo_objects.get.return_value = mock_repo

        mock_tag = MagicMock()
        mock_tag.id = 1
        mock_tag.name = "latest"
        mock_tag.digest = "sha256:abcd1234"
        mock_tag.compressed_size_mb = 145
        mock_tag.os_arch = "linux/amd64"
        mock_tag_objects.create.return_value = mock_tag

        request = MagicMock()
        # Kreiramo mock user sa username
        mock_user = MagicMock()
        mock_user.username = "fake_user"
        request.user = mock_user

        request.data = {
            "name": "latest",
            "digest": "sha256:abcd1234",
            "compressed_size_mb": 145,
            "os_arch": "linux/amd64"
        }

        view = RepositoryTagListView()
        response = view.post(request, pk=1)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == {
            "id": 1,
            "name": "latest",
            "digest": "sha256:abcd1234",
            "compressed_size_mb": 145,
            "os_arch": "linux/amd64"
        }
        mock_repo_objects.get.assert_called_once_with(pk=1)
        mock_tag_objects.create.assert_called_once_with(
            repository=mock_repo,
            name="latest",
            digest="sha256:abcd1234",
            compressed_size_mb=145,
            os_arch="linux/amd64"
        )

    # -------------------
    # POST metoda - negativni slučaj (repo ne postoji)
    # -------------------
    @patch("tag.views.Repository.objects")
    def test_post_tag_repository_not_found(self, mock_repo_objects):
        mock_repo_objects.get.side_effect = Repository.DoesNotExist

        request = MagicMock()
        # kreiramo user mock sa username atributom
        mock_user = MagicMock()
        mock_user.username = "fake_user"
        request.user = mock_user

        request.data = {
            "name": "latest",
            "digest": "sha256:abcd1234",
            "compressed_size_mb": 145,
            "os_arch": "linux/amd64"
        }

        view = RepositoryTagListView()
        response = view.post(request, pk=999)

        assert response.status_code == 404
        assert response.data == {"error": "Repository not found"}
        mock_repo_objects.get.assert_called_once_with(pk=999)
