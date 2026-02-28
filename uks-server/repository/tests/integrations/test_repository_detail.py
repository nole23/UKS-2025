from django.contrib.auth.models import Group
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from repository.models import Repository
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RepositoryDetailViewTests(APITestCase):

    def setUp(self):
        # Kreiraj korisnika sa unikatnim emailom
        self.user = User.objects.create_user(
            username="owner",
            password="pass",
            email="owner@example.com"
        )

        # Kreiraj repository
        self.repo = Repository.objects.create(
            name="repo",
            visibility="public",
            owner=self.user
        )

        # Generiši JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # Postavi header za autentifikaciju
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_get_repository(self):
        response = self.client.get(f"/api/repositories/{self.repo.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "repo")

    def test_delete_repository_owner(self):
        response = self.client.delete(f"/api/repositories/{self.repo.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Repository.objects.filter(id=self.repo.id).exists())
    
    def test_delete_repository_non_owner_forbidden(self):
        other_user = User.objects.create_user(username="other", email="other@example.com", password="pass")
        refresh = RefreshToken.for_user(other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        response = self.client.delete(f"/api/repositories/{self.repo.id}/")
        self.assertEqual(response.status_code, 403)

    def test_delete_repository_superadmin(self):
        superadmin = User.objects.create_user(username="admin", email="admin@example.com", password="pass")
        group, _ = Group.objects.get_or_create(name="Superadmin")
        superadmin.groups.add(group)
        refresh = RefreshToken.for_user(superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        response = self.client.delete(f"/api/repositories/{self.repo.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Repository.objects.filter(id=self.repo.id).exists())

    def test_get_nonexistent_repository(self):
        response = self.client.get(f"/api/repositories/99999/")
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_access(self):
        self.client.credentials()  # ukloni token

        response = self.client.get(f"/api/repositories/{self.repo.id}/")
        self.assertEqual(response.status_code, 401)

        response = self.client.delete(f"/api/repositories/{self.repo.id}/")
        self.assertEqual(response.status_code, 401)