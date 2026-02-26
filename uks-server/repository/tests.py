from unittest import TestCase
from unittest.mock import MagicMock, patch
from rest_framework import status
from django.db.models import Q
from repository.views import RepositoryListView, RepositoryDetailView, RepositorySearchView, RepositoryCollaboratorView
from .models import Repository, RepositoryCollaborator
from .serializer import RepositorySerializer
from django.contrib.auth.models import User


class RepositorySerializerUnitTests(TestCase):

    def setUp(self):
        # Kreiramo "mock" owner i organization
        self.mock_owner = MagicMock()
        self.mock_owner.username = "mockuser"

        self.mock_org = MagicMock()
        self.mock_org.name = "mockorg"

        # Kreiramo mock repository instancu
        self.mock_repo = MagicMock()
        self.mock_repo.id = 1
        self.mock_repo.name = "TestRepo"
        self.mock_repo.description = "A test repository"
        self.mock_repo.visibility = "public"
        self.mock_repo.created_at = "2026-02-07T12:00:00Z"
        self.mock_repo.owner = self.mock_owner
        self.mock_repo.organization = self.mock_org
        self.mock_repo.last_pushed_at = "2026-02-07T13:00:00Z"
        self.mock_repo.stars_count = 5
        self.mock_repo.pulls_count = 2

    def test_repository_serializer_fields(self):
        serializer = RepositorySerializer(instance=self.mock_repo)

        data = serializer.data
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["name"], "TestRepo")
        self.assertEqual(data["description"], "A test repository")
        self.assertEqual(data["visibility"], "public")
        self.assertEqual(data["created_at"], "2026-02-07T12:00:00Z")
        self.assertEqual(data["owner_username"], "mockuser")
        self.assertEqual(data["organization_name"], "mockorg")
        self.assertEqual(data["last_pushed_at"], "2026-02-07T13:00:00Z")
        self.assertEqual(data["stars_count"], 5)
        self.assertEqual(data["pulls_count"], 2)


class RepositoryModelMockTests(TestCase):

    def setUp(self):
        # Sve "instancirane" stvari su MagicMock
        self.user = MagicMock()
        self.user.username = "mockuser"

        self.org = MagicMock()
        self.org.name = "mockorg"

    def test_repository_creation(self):
        repo = MagicMock(spec=Repository)
        repo.name = "TestRepo"
        repo.description = "A test repository"
        repo.visibility = "public"
        repo.owner = self.user
        repo.organization = self.org

        self.assertEqual(repo.name, "TestRepo")
        self.assertEqual(repo.visibility, "public")
        self.assertEqual(repo.owner.username, "mockuser")
        self.assertEqual(repo.organization.name, "mockorg")

    def test_collaborator_creation(self):
        repo = MagicMock(spec=Repository)
        user = MagicMock()
        user.username = "collabuser"

        collaborator = MagicMock(spec=RepositoryCollaborator)
        collaborator.repository = repo
        collaborator.user = user
        collaborator.role = "admin"

        self.assertEqual(collaborator.role, "admin")
        self.assertEqual(collaborator.repository, repo)
        self.assertEqual(collaborator.user.username, "collabuser")

    def test_collaborator_unique_together(self):
        repo = MagicMock(spec=Repository)
        user = MagicMock()
        user.username = "user2"

        collaborator1 = MagicMock(spec=RepositoryCollaborator)
        collaborator1.repository = repo
        collaborator1.user = user
        collaborator1.role = "read"

        collaborator2 = MagicMock(spec=RepositoryCollaborator)
        collaborator2.repository = repo
        collaborator2.user = user
        collaborator2.role = "read"

        self.assertEqual(collaborator1.repository, collaborator2.repository)
        self.assertEqual(collaborator1.user, collaborator2.user)
    

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
    @patch("repository.views.safe_delete_pattern")
    @patch("repository.views.RepositorySerializer")
    @patch("repository.views.Organization.objects.get")
    def test_post_create_repository_positive(self, mock_org_get, mock_serializer_class, mock_safe_delete):
        mock_org_get.return_value = None

        # mock user objekat
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.is_superadmin = False

        # serializer mock
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {"name": "testuser/NewRepo", "owner": 1}
        mock_serializer_class.return_value = mock_serializer

        request = MagicMock()
        request.user = mock_user
        request.data = {"name": "NewRepo", "visibility": "public"}

        view = RepositoryListView()
        response = view.post(request)

        # status
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # serializer poziv
        mock_serializer_class.assert_called_once_with(data={
            "name": "testuser/NewRepo",
            "visibility": "public",
            "official": False
        })

        # save poziv
        mock_serializer.save.assert_called_once_with(
            owner=mock_user,
            organization=None,
            official=False
        )

        # cache invalidation
        self.assertEqual(mock_safe_delete.call_count, 2)


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


class RepositorySearchViewUnitTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.cache")
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_search_repositories_positive(self, mock_serializer_class, mock_repo_objects, mock_collab_objects, mock_cache):
        # ---------- USER ----------
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_superadmin = False
        mock_user.is_admin.return_value = False

        # ---------- CACHE MISS ----------
        mock_cache.get.return_value = None

        # ---------- COLLAB IDS ----------
        mock_collab_qs = MagicMock()
        mock_collab_qs.values_list.return_value = []
        mock_collab_objects.filter.return_value = mock_collab_qs

        # ---------- QUERYSET ----------
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs

        mock_repo_objects.filter.return_value = mock_qs

        # ---------- SERIALIZER ----------
        mock_serializer = MagicMock()
        mock_serializer.data = [{"name": "Repo1"}, {"name": "Repo2"}]
        mock_serializer_class.return_value = mock_serializer

        # ---------- REQUEST ----------
        request = MagicMock()
        request.user = mock_user
        request.query_params = {"q": "Repo"}

        # ---------- VIEW ----------
        view = RepositorySearchView()
        response = view.get(request)

        # ---------- ASSERT ----------
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{"name": "Repo1"}, {"name": "Repo2"}])

        mock_repo_objects.filter.assert_called()      # base filter
        self.assertTrue(mock_qs.filter.called)        # search filter
        self.assertTrue(mock_qs.order_by.called)      # sorting

        mock_serializer_class.assert_called_once_with(mock_qs, many=True)
        mock_cache.set.assert_called_once()           # cache stored


    # -------------------
    # GET metoda - negativni slučaj (prazna pretraga)
    # -------------------
    @patch("repository.views.cache")
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_search_repositories_negative(self, mock_serializer_class, mock_repo_objects, mock_collab_objects, mock_cache):
        # cache miss
        mock_cache.get.return_value = None

        # collaborator ids
        mock_collab_objects.filter.return_value.values_list.return_value = []

        # queryset chain
        mock_queryset = MagicMock()
        mock_repo_objects.filter.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.prefetch_related.return_value = mock_queryset

        # serializer
        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_serializer_class.return_value = mock_serializer

        # mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_superadmin = False
        mock_user.is_admin.return_value = False

        # request
        request = MagicMock()
        request.user = mock_user
        request.query_params = {"q": ""}

        # call view
        view = RepositorySearchView()
        response = view.get(request)

        # assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        mock_repo_objects.filter.assert_called()
        mock_queryset.order_by.assert_called_once_with("-created_at")
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
        mock_repo.owner = "fake_user"
        mock_repo_objects.get.return_value = mock_repo

        request = MagicMock()
        request.user = "fake_user"

        view = RepositoryDetailView()
        response = view.delete(request, pk=1)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_repo.delete.assert_called_once()


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
        mock_repo.owner = MagicMock()
        mock_repo_objects.get.return_value = mock_repo

        mock_user = MagicMock()
        mock_user.groups.filter.return_value.exists.return_value = False

        request = MagicMock()
        request.user = mock_user
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
        mock_repo.owner = MagicMock()  # owner nije isti user
        mock_repo_objects.get.return_value = mock_repo

        mock_user = MagicMock()
        mock_user.groups.filter.return_value.exists.return_value = False

        request = MagicMock()
        request.user = mock_user

        view = RepositoryCollaboratorView()
        response = view.delete(request, pk=1, user_id=123)

        assert response.status_code == status.HTTP_403_FORBIDDEN
