from unittest import TestCase
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
        # Mock query set sa jednim public repo
        mock_queryset = MagicMock()
        mock_objects.filter.return_value.order_by.return_value = mock_queryset

        # Mock serializer
        mock_serializer = MagicMock()
        mock_serializer.data = [{"name": "PublicRepo"}]
        mock_serializer_class.return_value = mock_serializer

        # Fake request
        request = MagicMock()
        request.user = "fake_user"

        view = RepositoryListView()
        response = view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{"name": "PublicRepo"}])
        mock_objects.filter.assert_called_once_with(visibility="public")
        mock_objects.filter.return_value.order_by.assert_called_once_with("-created_at")
        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)

    # -------------------
    # GET metoda - negativni slučaj
    # -------------------
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_public_repositories_negative(self, mock_serializer_class, mock_objects):
        # Mock query set je prazan
        mock_queryset = MagicMock()
        mock_objects.filter.return_value.order_by.return_value = mock_queryset

        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_serializer_class.return_value = mock_serializer

        request = MagicMock()
        request.user = "fake_user"

        view = RepositoryListView()
        response = view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        mock_objects.filter.assert_called_once_with(visibility="public")
        mock_objects.filter.return_value.order_by.assert_called_once_with("-created_at")
        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)

    # -------------------
    # POST metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.RepositorySerializer")
    @patch("repository.views.Organization.objects.get")
    def test_post_create_repository_positive(self, mock_org_get, mock_serializer_class):
        mock_org_get.return_value = None  # ne koristimo org u ovom testu

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {"name": "NewRepo", "owner": 1}
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer

        request = MagicMock()
        request.user = "fake_user"
        request.data = {"name": "NewRepo", "visibility": "public"}

        view = RepositoryListView()
        response = view.post(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"name": "NewRepo", "owner": 1})
        
        # Ovo je ključna promena
        mock_serializer_class.assert_called_once_with(data=request.data)
        
        mock_serializer.save.assert_called_once_with(owner="fake_user", organization=None)


    # -------------------
    # POST metoda - negativni slučaj (organization ne postoji)
    # -------------------
    @patch("repository.views.Organization.objects.get")
    def test_post_create_repository_invalid_org(self, mock_org_get):
        from Organization.models import Organization
        # Baca exception kao da ne postoji
        mock_org_get.side_effect = Organization.DoesNotExist

        request = MagicMock()
        request.user = "fake_user"
        request.data = {"name": "RepoWithOrg", "visibility": "public", "organization_id": 999}

        view = RepositoryListView()
        response = view.post(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Organization not found"})


from unittest import TestCase
from unittest.mock import MagicMock, patch
from rest_framework import status
from repository.views import RepositorySearchView
from django.db.models import Q

class RepositorySearchViewUnitTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_search_repositories_positive(self, mock_serializer_class, mock_objects):
        # Kreiramo "duboki" mock QuerySet
        mock_queryset = MagicMock()
        # Svaki poziv filter vraća isti mock (chainable)
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset

        mock_objects.filter.return_value = mock_queryset

        mock_serializer = MagicMock()
        mock_serializer.data = [{"name": "Repo1"}, {"name": "Repo2"}]
        mock_serializer_class.return_value = mock_serializer

        request = MagicMock()
        request.user = "fake_user"
        request.query_params = {"q": "Repo"}

        view = RepositorySearchView()
        response = view.get(request)

        # Proveravamo rezultat
        assert response.status_code == status.HTTP_200_OK
        assert response.data == [{"name": "Repo1"}, {"name": "Repo2"}]

        # Proveravamo da su filter i order_by pozvani bar jednom
        mock_objects.filter.assert_called()  # filter visibility
        mock_queryset.filter.assert_called()  # filter Q objekt
        mock_queryset.order_by.assert_called()  # order_by na finalnom QuerySet

        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)


    # -------------------
    # GET metoda - negativni slučaj (prazna pretraga)
    # -------------------
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_search_repositories_negative(self, mock_serializer_class, mock_objects):
        mock_queryset = MagicMock()
        mock_objects.filter.return_value.order_by.return_value = mock_queryset

        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_serializer_class.return_value = mock_serializer

        request = MagicMock()
        request.user = "fake_user"
        request.query_params = {"q": ""}

        view = RepositorySearchView()
        response = view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        mock_objects.filter.assert_called()
        mock_objects.filter.return_value.order_by.assert_called_once_with('-created_at')
        mock_serializer_class.assert_called_once_with(mock_queryset, many=True)
