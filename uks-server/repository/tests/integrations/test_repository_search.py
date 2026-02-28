from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from repository.models import Repository, RepositoryCollaborator
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RepositorySearchViewTests(APITestCase):

    def setUp(self):
        # ---------- Users ----------
        self.superadmin = User.objects.create_user(username="superadmin", email="super@example.com", password="pass")
        self.admin = User.objects.create_user(username="admin", email="admin@example.com", password="pass")
        self.user = User.objects.create_user(username="user", email="user@example.com", password="pass")

        # Assign groups
        self.superadmin.groups.create(name="Superadmin")
        self.admin.groups.create(name="Administrator")
        self.user.groups.create(name="OrdinaryUser")

        # Generate JWT tokens
        self.superadmin_token = str(RefreshToken.for_user(self.superadmin).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)
        self.user_token = str(RefreshToken.for_user(self.user).access_token)

        # ---------- Repositories ----------
        # public and private repos
        self.repo_public = Repository.objects.create(name="public_repo", visibility="public", owner=self.user, badge="OFFICIAL", stars_count=5)
        self.repo_private = Repository.objects.create(name="private_repo", visibility="private", owner=self.user, badge="VERIFIED", stars_count=2)
        self.repo_admin = Repository.objects.create(name="admin_repo", visibility="public", owner=self.admin, badge="SPONSORED", stars_count=10)
        self.repo_superadmin = Repository.objects.create(name="superadmin_repo", visibility="private", owner=self.superadmin, badge="OFFICIAL", stars_count=20)

        # collaborator
        RepositoryCollaborator.objects.create(user=self.user, repository=self.repo_admin)

    # ---------- HELPERS ----------
    def get_response(self, user_token, params=None):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        params = params or {}
        # Dodaj limit=10 da DRF paginacija uvek vrati dict sa "results"
        params.setdefault("limit", 10)
        return self.client.get("/api/repositories/search/", params, format="json")

    # ---------- TESTS ----------
    def test_superadmin_sees_all_repos(self):
        response = self.get_response(self.superadmin_token)
        self.assertEqual(response.status_code, 200)
        repo_names = [r["name"] for r in response.data["results"]]
        expected = [self.repo_public.name, self.repo_private.name, self.repo_admin.name, self.repo_superadmin.name]
        self.assertCountEqual(repo_names, expected)

    def test_admin_sees_only_public_repos(self):
        response = self.get_response(self.admin_token)
        self.assertEqual(response.status_code, 200)
        repo_names = [r["name"] for r in response.data["results"]]
        # admin vidi samo public
        expected = [self.repo_public.name, self.repo_admin.name]
        self.assertCountEqual(repo_names, expected)

    def test_user_sees_public_owned_and_collaborator_repos(self):
        response = self.get_response(self.user_token)
        self.assertEqual(response.status_code, 200)
        repo_names = [r["name"] for r in response.data["results"]]
        expected = [self.repo_public.name, self.repo_private.name, self.repo_admin.name]
        self.assertCountEqual(repo_names, expected)

    def test_search_filter_by_badge(self):
        response = self.get_response(self.user_token, {"badge": "OFFICIAL"})
        repo_names = [r["name"] for r in response.data["results"]]
        self.assertIn(self.repo_public.name, repo_names)
        self.assertNotIn(self.repo_private.name, repo_names)

    def test_search_filter_visibility_public(self):
        response = self.get_response(self.user_token, {"visibility": "public"})
        repo_names = [r["name"] for r in response.data["results"]]
        for r in repo_names:
            repo_obj = Repository.objects.get(name=r)
            self.assertEqual(repo_obj.visibility, "public")

    def test_search_query_matches_name_description(self):
        self.repo_public.description = "special keyword here"
        self.repo_public.save()
        response = self.get_response(self.user_token, {"q": "special"})
        repo_names = [r["name"] for r in response.data["results"]]
        self.assertIn(self.repo_public.name, repo_names)

    def test_search_sorting_oldest(self):
        response = self.get_response(self.user_token, {"sorting": "oldest"})
        repo_names = [r["name"] for r in response.data["results"]]
        created_dates = [Repository.objects.get(name=name).created_at for name in repo_names]
        self.assertEqual(created_dates, sorted(created_dates))

    def test_search_random_sorting(self):
        # random test: samo proveravamo da endpoint radi bez greske
        response = self.get_response(self.user_token, {"sorting": "random"})
        self.assertEqual(response.status_code, 200)