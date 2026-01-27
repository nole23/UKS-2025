from unittest import TestCase
from unittest.mock import MagicMock, patch
from rest_framework import status
from repository.views import RepositoryListView, RepositoryDetailView


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



class RepositoryDetailViewTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_repository_positive(self, mock_serializer_class, mock_repo_objects):
        mock_repo = MagicMock()
        mock_repo_objects.get.return_value = mock_repo

        mock_serializer = MagicMock()
        mock_serializer.data = {"id": 1, "name": "Repo1"}
        mock_serializer_class.return_value = mock_serializer

        request = MagicMock()
        request.user = "fake_user"

        view = RepositoryDetailView()
        response = view.get(request, pk=1)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"id": 1, "name": "Repo1"}

        mock_repo_objects.get.assert_called_once_with(pk=1)
        mock_serializer_class.assert_called_once_with(mock_repo)

    # -------------------
    # DELETE metoda - negativni slučaj (user nije owner)
    # -------------------
    @patch("repository.views.Repository.objects")
    def test_delete_repository_forbidden(self, mock_repo_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "other_user"
        mock_repo_objects.get.return_value = mock_repo

        request = MagicMock()
        request.user = "fake_user"  # nije owner

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
        mock_repo.owner = "fake_user"
        mock_repo_objects.get.return_value = mock_repo

        request = MagicMock()
        request.user = "fake_user"

        view = RepositoryDetailView()
        response = view.delete(request, pk=1)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_repo.delete.assert_called_once()


from unittest import TestCase
from unittest.mock import MagicMock, patch
from rest_framework import status
from repository.views import RepositoryCollaboratorView
from repository.models import Repository, RepositoryCollaborator
from django.contrib.auth.models import User


class RepositoryCollaboratorViewTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.RepositoryCollaborator.objects")
    def test_get_collaborators_positive(self, mock_collab_objects):
        collab1 = MagicMock()
        collab1.user.id = 1
        collab1.user.username = "user1"

        collab2 = MagicMock()
        collab2.user.id = 2
        collab2.user.username = "user2"

        mock_collab_objects.filter.return_value = [collab1, collab2]

        request = MagicMock()
        request.user = "fake_user"

        view = RepositoryCollaboratorView()
        response = view.get(request, pk=1)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == [
            {"id": 1, "username": "user1"},
            {"id": 2, "username": "user2"},
        ]
        mock_collab_objects.filter.assert_called_once_with(repository_id=1)

    # -------------------
    # POST metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.User.objects")
    @patch("repository.views.Repository.objects")
    def test_post_collaborator_positive(self, mock_repo_objects, mock_user_objects, mock_collab_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "fake_user"
        mock_repo_objects.get.return_value = mock_repo

        mock_user = MagicMock()
        mock_user_objects.get.return_value = mock_user

        mock_collab_objects.get_or_create.return_value = (MagicMock(), True)

        request = MagicMock()
        request.user = "fake_user"
        request.data = {"user_id": 123}

        view = RepositoryCollaboratorView()
        response = view.post(request, pk=1)

        assert response.status_code == 200
        assert response.data == {"message": "Collaborator added"}
        mock_collab_objects.get_or_create.assert_called_once_with(repository=mock_repo, user=mock_user)

    # -------------------
    # POST metoda - negativni slučaj (user nije owner)
    # -------------------
    @patch("repository.views.Repository.objects")
    def test_post_collaborator_forbidden(self, mock_repo_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "other_user"
        mock_repo_objects.get.return_value = mock_repo

        request = MagicMock()
        request.user = "fake_user"
        request.data = {"user_id": 123}

        view = RepositoryCollaboratorView()
        response = view.post(request, pk=1)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # -------------------
    # DELETE metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    def test_delete_collaborator_positive(self, mock_repo_objects, mock_collab_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "fake_user"
        mock_repo_objects.get.return_value = mock_repo

        mock_collab_qs = MagicMock()
        mock_collab_objects.filter.return_value = mock_collab_qs

        request = MagicMock()
        request.user = "fake_user"

        view = RepositoryCollaboratorView()
        response = view.delete(request, pk=1, user_id=123)

        assert response.status_code == 200
        assert response.data == {"message": "Collaborator removed"}
        mock_collab_objects.filter.assert_called_once_with(repository=mock_repo, user_id=123)
        mock_collab_qs.delete.assert_called_once()

    # -------------------
    # DELETE metoda - negativni slučaj (user nije owner)
    # -------------------
    @patch("repository.views.Repository.objects")
    def test_delete_collaborator_forbidden(self, mock_repo_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "other_user"
        mock_repo_objects.get.return_value = mock_repo

        request = MagicMock()
        request.user = "fake_user"

        view = RepositoryCollaboratorView()
        response = view.delete(request, pk=1, user_id=123)

        assert response.status_code == status.HTTP_403_FORBIDDEN
