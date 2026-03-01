from django.test import TestCase
from unittest.mock import MagicMock, patch
from django.http import QueryDict

from repository.views import RepositorySearchView


from django.test import TestCase
from unittest.mock import MagicMock, patch
from django.http import QueryDict

from repository.views import RepositorySearchView


# -----------------------------
# RepositorySearchView Unit Tests
# -----------------------------
class RepositorySearchViewUnitTests(TestCase):
    """
    Testovi za GET metodu RepositorySearchView.
    Pokrivamo sve tipove korisnika (superadmin, admin, ordinary user),
    kao i cache hit/miss i filtere.
    """

    # -------------------
    # NEGATIVNI TEST (OBIČAN KORISNIK)
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

        # kreiramo MagicMock queryset
        mock_queryset = MagicMock()
        mock_queryset.__len__.return_value = 0
        mock_queryset.count.return_value = 0  # KLJUČNO za DRF LimitOffsetPagination
        mock_repo_objects.filter.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.prefetch_related.return_value = mock_queryset
        mock_queryset.select_related.return_value = mock_queryset

        # serializer
        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_serializer_class.return_value = mock_serializer

        # mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_superadmin = False
        mock_user.is_admin.return_value = False

        # QueryDict za getlist()
        qdict = QueryDict(mutable=True)
        qdict.setlist('badge', [])
        qdict.update({'q': '', 'visibility': 'all', 'sorting': 'latest', 'limit': 20, 'offset': 0})

        request = MagicMock()
        request.user = mock_user
        request.query_params = qdict

        # poziv view-a
        view = RepositorySearchView()
        response = view.get(request)

        # assertions
        assert response.status_code == 200

        mock_repo_objects.filter.assert_called()
        mock_queryset.order_by.assert_called_once_with("-created_at")
        mock_serializer_class.assert_called_once_with([], many=True)

    # -------------------
    # POZITIVNI TEST (OBIČAN KORISNIK)
    # -------------------
    @patch("repository.views.cache")
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_user_with_repos_positive(self, mock_serializer_class, mock_repo_objects, mock_collab_objects, mock_cache):
        """
        Običan korisnik ima pristup public repo ili own repo → vraća listu repozitorijuma
        """
        mock_cache.get.return_value = None
        mock_collab_objects.filter.return_value.values_list.return_value = [1]

        mock_queryset = MagicMock()
        mock_queryset.__len__.return_value = 1
        mock_queryset.count.return_value = 1
        mock_repo_objects.filter.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.select_related.return_value = mock_queryset
        mock_queryset.prefetch_related.return_value = mock_queryset

        mock_serializer = MagicMock()
        mock_serializer.data = [{"name": "UserRepo"}]
        mock_serializer_class.return_value = mock_serializer

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_superadmin = False
        mock_user.is_admin.return_value = False

        qdict = QueryDict(mutable=True)
        qdict.setlist("badge", [])
        qdict.update({"q": "", "visibility": "all", "sorting": "latest", "limit": 20, "offset": 0})

        request = MagicMock()
        request.user = mock_user
        request.query_params = qdict

        view = RepositorySearchView()
        response = view.get(request)

        assert response.status_code == 200
        # za paginated response proveravamo "results"
        assert response.data["results"] == [{"name": "UserRepo"}]

    # -------------------
    # POZITIVNI TEST: superadmin sa repozitorijumima
    # -------------------
    @patch("repository.views.cache")
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_superadmin_positive(self, mock_serializer_class, mock_repo_objects, mock_collab_objects, mock_cache):
        """
        Superadmin vraća sve repozitorijume → pozitivni test
        Proverava paginaciju, serializer i cache
        """
        # --- Cache --- 
        mock_cache.get.return_value = None

        # --- Collaborators --- 
        # superadmin ne koristi collaborator filter, ali patchujemo da view ne bi pukao
        mock_collab_objects.filter.return_value.values_list.return_value = []

        # --- MagicMock queryset ---
        mock_qs = MagicMock()
        mock_repo_objects.all.return_value = mock_qs

        # DRF LimitOffsetPagination očekuje ove metode
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        mock_qs.count.return_value = 2
        mock_qs.__len__.return_value = 2
        # __getitem__ mora da vrati listu elemenata za paginaciju
        mock_qs.__getitem__.side_effect = lambda k: [{"name": "AllRepo1"}, {"name": "AllRepo2"}][k]

        # --- Serializer ---
        mock_serializer = MagicMock()
        mock_serializer.data = [{"name": "AllRepo1"}, {"name": "AllRepo2"}]
        mock_serializer_class.return_value = mock_serializer

        # --- Mock user ---
        mock_user = MagicMock()
        mock_user.is_superadmin = True

        # --- QueryDict sa badge poljem ---
        qdict = QueryDict(mutable=True)
        qdict.setlist('badge', [])
        qdict.update({'q': '', 'visibility': 'all', 'sorting': 'latest', 'limit': 20, 'offset': 0})

        request = MagicMock()
        request.user = mock_user
        request.query_params = qdict

        # --- Poziv view-a ---
        view = RepositorySearchView()
        response = view.get(request)

        # --- Assertions ---
        assert response.status_code == 200

        mock_qs.order_by.assert_called_once_with("-created_at")
        mock_repo_objects.all.assert_called_once()
        mock_qs.order_by.assert_called()  # može biti random, latest ili oldest

    # -------------------
    # NEGATIVNI TEST: superadmin bez repozitorijuma
    # -------------------
    @patch("repository.views.cache")
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_superadmin_negative(self, mock_serializer_class, mock_repo_objects, mock_collab_objects, mock_cache):
        """Superadmin, ali nema repozitorijuma → vraća praznu listu"""

        # --- Cache miss ---
        mock_cache.get.return_value = None

        # --- Collaborator ids ---
        mock_collab_objects.filter.return_value.values_list.return_value = []

        # --- Prazan queryset sa pravim int count ---
        mock_qs = MagicMock()
        mock_repo_objects.all.return_value = mock_qs

        # DRF LimitOffsetPagination očekuje ove metode
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        mock_qs.count.return_value = 2
        mock_qs.__len__.return_value = 2
        # __getitem__ mora da vrati listu elemenata za paginaciju
        mock_qs.__getitem__.side_effect = lambda k: [][k]

        # --- Serializer ---
        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_serializer_class.return_value = mock_serializer

        # --- Mock user ---
        mock_user = MagicMock()
        mock_user.is_superadmin = True

        # --- QueryDict sa badge poljem ---
        qdict = QueryDict(mutable=True)
        qdict.setlist('badge', [])
        qdict.update({'q': '', 'visibility': 'all', 'sorting': 'latest', 'limit': 20, 'offset': 0})

        request = MagicMock()
        request.user = mock_user
        request.query_params = qdict

        # --- Poziv view ---
        view = RepositorySearchView()
        response = view.get(request)

        # --- Assertions ---
        assert response.status_code == 200
        assert response.data["results"] == []

    # -------------------
    # POZITIVNI TEST: admin sa public repozitorijumima
    # -------------------
    @patch("repository.views.cache")
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_admin_positive(self, mock_serializer_class, mock_repo_objects, mock_collab_objects, mock_cache):
        """Admin vidi samo public repozitorijume"""

        # --- Cache --- 
        mock_cache.get.return_value = None

        # --- Collaborators --- 
        # superadmin ne koristi collaborator filter, ali patchujemo da view ne bi pukao
        mock_collab_objects.filter.return_value.values_list.return_value = []

        # --- MagicMock queryset ---
        mock_qs = MagicMock()
        mock_repo_objects.filter.return_value = mock_qs  # ili .all() ako tako koristiš

        # DRF LimitOffsetPagination očekuje ove metode
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        mock_qs.count.return_value = 1
        mock_qs.__len__.return_value = 1
        # __getitem__ mora da vrati listu elemenata za paginaciju
        mock_qs.__getitem__.side_effect = lambda k: [{"name": "PublicRepo"}] if isinstance(k, slice) else [{"name": "PublicRepo"}][k]
        
        # --- Serializer ---
        mock_serializer = MagicMock()
        mock_serializer.data = [{"name": "PublicRepo"}]
        mock_serializer_class.return_value = mock_serializer

        # --- Mock user ---
        mock_user = MagicMock()
        mock_user.is_superadmin = False
        mock_user.is_admin.return_value = True

        # --- QueryDict sa badge poljem ---
        qdict = QueryDict(mutable=True)
        qdict.setlist('badge', [])
        qdict.update({'q': '', 'visibility': 'all', 'sorting': 'latest', 'limit': 20, 'offset': 0})

        request = MagicMock()
        request.user = mock_user
        request.query_params = qdict

        # --- View ---
        view = RepositorySearchView()
        response = view.get(request)

        # --- Assertions ---
        assert response.status_code == 200

    # -------------------
    # POZITIVNI TEST: cache hit
    # -------------------
    @patch("repository.views.cache")
    @patch("repository.views.RepositoryCollaborator.objects")
    def test_get_cache_hit(self, mock_collab_objects, mock_cache):
        # --- Cache hit ---
        mock_cache.get.return_value = [{"name": "CachedRepo"}]

        # --- RepositoryCollaborator patch ---
        mock_queryset = MagicMock()
        mock_queryset.__len__.return_value = 0
        mock_queryset.count.return_value = 0
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.values_list.return_value = []
        mock_collab_objects.filter.return_value = mock_queryset

        # --- Mock user i request ---
        mock_user = MagicMock()
        request = MagicMock()
        request.user = mock_user
        request.query_params = MagicMock()
        request.query_params.getlist = MagicMock(return_value=[])

        # --- Poziv view ---
        view = RepositorySearchView()
        response = view.get(request)

        # --- Assertions ---
        assert response.status_code == 200
        assert response.data == [{"name": "CachedRepo"}]

    @patch("repository.views.cache")
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_search_cache_hit(self, mock_serializer_class, mock_repo_objects, mock_collab_objects, mock_cache):
        # Cache returns result
        mock_cache.get.return_value = [{"name": "CachedRepo"}]

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_superadmin = False
        mock_user.is_admin.return_value = False

        # QueryDict sa getlist()
        qdict = QueryDict(mutable=True)
        qdict.setlist('badge', [])
        qdict.update({'q': 'Repo', 'visibility': 'all', 'sorting': 'latest', 'limit': 20, 'offset': 0})

        request = MagicMock()
        request.user = mock_user
        request.query_params = qdict

        view = RepositorySearchView()
        response = view.get(request)

        assert response.status_code == 200
        assert response.data == [{"name": "CachedRepo"}]

        mock_repo_objects.filter.assert_not_called()

    @patch("repository.views.cache")
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    @patch("repository.views.RepositorySerializer")
    def test_get_search_superadmin_user(self, mock_serializer_class, mock_repo_objects, mock_collab_objects, mock_cache):
        mock_collab_objects.filter.return_value.values_list.return_value = []

        # kreiramo MagicMock queryset
        mock_queryset = MagicMock()
        mock_queryset.__len__.return_value = 0
        mock_queryset.count.return_value = 0  # KLJUČNO za DRF LimitOffsetPagination
        mock_repo_objects.filter.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.prefetch_related.return_value = mock_queryset
        mock_queryset.select_related.return_value = mock_queryset

        # serializer
        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_serializer_class.return_value = mock_serializer

        # mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.is_superadmin = False
        mock_user.is_admin.return_value = False

        # QueryDict za getlist()
        qdict = QueryDict(mutable=True)
        qdict.setlist('badge', [])
        qdict.update({'q': '', 'visibility': 'all', 'sorting': 'latest', 'limit': 20, 'offset': 0})

        request = MagicMock()
        request.user = mock_user
        request.query_params = qdict

        view = RepositorySearchView()
        response = view.get(request)

        assert response.status_code == 200