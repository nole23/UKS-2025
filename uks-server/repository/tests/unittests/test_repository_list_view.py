from django.test import TestCase
from unittest.mock import MagicMock, patch
from rest_framework import status
from repository.views import RepositoryListView

class RepositoryListViewUnitTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_public_repositories_positive(self, mock_serializer_class, mock_objects):
        # Mock queryset i serializer
        mock_queryset = MagicMock()
        mock_objects.filter.return_value.order_by.return_value = mock_queryset

        mock_serializer = MagicMock()
        mock_serializer.data = [{"name": "PublicRepo"}]
        mock_serializer_class.return_value = mock_serializer

        # Mock user sa username
        mock_user = MagicMock()
        mock_user.username = "fake_user"

        # Mock request
        request = MagicMock()
        request.user = mock_user  # <- VAŽNO

        # Pokreni view
        view = RepositoryListView()
        response = view.get(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [{"name": "PublicRepo"}]

    # -------------------
    # GET metoda - negativni slučaj
    # -------------------
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_public_repositories_negative(self, mock_serializer_class, mock_objects):
        mock_queryset = MagicMock()
        mock_objects.filter.return_value.order_by.return_value = mock_queryset

        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_serializer_class.return_value = mock_serializer

        # Mock user sa username
        mock_user = MagicMock()
        mock_user.username = "fake_user"

        # Mock request
        request = MagicMock()
        request.user = mock_user  # <- VAŽNO

        view = RepositoryListView()
        response = view.get(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

        mock_objects.filter.assert_called_once_with(visibility="public")
        mock_objects.filter.return_value.order_by.assert_called_once_with("-created_at")
        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)

    # -------------------
    # POST metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.safe_delete_pattern")
    @patch("repository.views.RepositorySerializer")
    @patch("repository.views.Organization.objects.get")
    def test_post_create_repository_positive(self, mock_org_get, mock_serializer_class, mock_safe_delete):
        mock_org_get.return_value = None
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_class.return_value = mock_serializer
        request = MagicMock()
        request.user = mock_user
        request.data = {"name": "NewRepo", "visibility": "public"}
        view = RepositoryListView()
        response = view.post(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # official više nije prosleđen, samo badge, owner i organization
        mock_serializer.save.assert_called_once_with(
            owner=mock_user,
            organization=None,
            badge="NONE"
        )

    # -------------------
    # POST metoda - negativni slučaj (organization ne postoji)
    # -------------------
    @patch("repository.views.Organization.objects.get")
    def test_post_create_repository_invalid_org(self, mock_org_get):
        from Organization.models import Organization
        mock_org_get.side_effect = Organization.DoesNotExist

        # Korisnik je MagicMock sa username
        mock_user = MagicMock()
        mock_user.username = "fake_user"

        request = MagicMock()
        request.user = mock_user
        request.data = {"name": "RepoWithOrg", "visibility": "public", "organization_id": 999}

        view = RepositoryListView()
        response = view.post(request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Organization not found"}

    # -------------------
    # POST metoda - official repo superadmin
    # -------------------
    @patch("repository.views.safe_delete_pattern")
    @patch("repository.views.RepositorySerializer")
    @patch("repository.views.Organization.objects.get")
    def test_post_create_official_repo_superadmin(self, mock_org_get, mock_serializer_class, mock_safe_delete):
        mock_org_get.return_value = None
        mock_user = MagicMock()
        mock_user.username = "adminuser"
        mock_user.is_superadmin = True
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_class.return_value = mock_serializer
        request = MagicMock()
        request.user = mock_user
        request.data = {"name": "OfficialRepo", "visibility": "public", "official": True}
        view = RepositoryListView()
        response = view.post(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_serializer.save.assert_called_once_with(
            owner=mock_user,
            organization=None,
            badge="NONE"
        )

    # -------------------
    # POST metoda - sa organizacijom
    # -------------------
    @patch("repository.views.safe_delete_pattern")
    @patch("repository.views.RepositorySerializer")
    @patch("repository.views.Organization.objects.get")
    def test_post_create_repo_with_org(self, mock_org_get, mock_serializer_class, mock_safe_delete):
        mock_org = MagicMock()
        mock_org_get.return_value = mock_org
        mock_user = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_class.return_value = mock_serializer
        request = MagicMock()
        request.user = mock_user
        request.data = {"name": "RepoWithOrg", "visibility": "public", "organization_id": 1}
        view = RepositoryListView()
        response = view.post(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_serializer.save.assert_called_once_with(
            owner=None,
            organization=mock_org,
            badge="NONE"
        )

    # -------------------
    # POST metoda - verified badge
    # -------------------
    @patch("repository.views.safe_delete_pattern")
    @patch("repository.views.RepositorySerializer")
    @patch("repository.views.Organization.objects.get")
    def test_post_create_repo_with_verified_badge(self, mock_org_get, mock_serializer_class, mock_safe_delete):
        mock_org_get.return_value = None
        mock_user = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_class.return_value = mock_serializer
        request = MagicMock()
        request.user = mock_user
        request.data = {"name": "RepoBadge", "visibility": "public", "badge": "VERIFIED"}
        view = RepositoryListView()
        response = view.post(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_serializer.save.assert_called_once_with(
            owner=mock_user,
            organization=None,
            badge="VERIFIED"
        )