from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from repository.models import Repository, Organization
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import Group

User = get_user_model()

class RepositoryListViewTests(APITestCase):

    def setUp(self):
        # običan korisnik
        self.user = User.objects.create_user(
            username="user",
            password="pass",
            email="user@example.com"
        )

        # 1. Kreiraj korisnika
        self.superadmin = User.objects.create_user(username="admin", password="pass")

        # 2. Dodaj korisnika u Superadmin grupu
        group, _ = Group.objects.get_or_create(name="Superadmin")
        self.superadmin.groups.add(group)
        self.superadmin.save()
        # JWT tokeni
        self.user_token = str(RefreshToken.for_user(self.user).access_token)
        self.superadmin_token = str(RefreshToken.for_user(self.superadmin).access_token)

        # Organizacija
        self.org = Organization.objects.create(name="TestOrg", owner=self.user)

        # Test repozitorijumi
        Repository.objects.create(name="repo1", visibility="public")
        Repository.objects.create(name="repo2", visibility="private")

    # =========================
    # GET TESTS
    # =========================
    def test_get_only_public_repositories(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        response = self.client.get("/api/repositories")
        self.assertEqual(response.status_code, 200)
        public_repos = Repository.objects.filter(visibility="public")
        self.assertEqual(len(response.data), public_repos.count())

    def test_get_with_query_param(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        response = self.client.get("/api/repositories?q=repo1")
        self.assertEqual(response.status_code, 200)
        # svi public repozitorijumi su vraćeni, filtriranje se ne radi na query param
        self.assertTrue(all(r["visibility"] == "public" for r in response.data))

    # =========================
    # POST TESTS - običan korisnik
    # =========================
    def test_post_regular_user_creates_repo(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        payload = {
            "name": "newrepo",
            "description": "desc",
            "visibility": "public"
        }
        response = self.client.post("/api/repositories", payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Repository.objects.filter(name="user/newrepo").exists())
        repo = Repository.objects.get(name="user/newrepo")
        self.assertEqual(repo.badge, "NONE")
        self.assertEqual(repo.owner, self.user)

    def test_post_with_invalid_organization(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        payload = {
            "name": "newrepo",
            "organization_id": 9999
        }
        response = self.client.post("/api/repositories", payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Organization not found", response.data["error"])

    def test_post_invalid_data(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        payload = {}  # prazno telo
        response = self.client.post("/api/repositories", payload)
        self.assertEqual(response.status_code, 400)