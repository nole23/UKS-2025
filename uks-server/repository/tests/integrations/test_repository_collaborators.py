from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from repository.models import Repository, RepositoryCollaborator
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RepositoryCollaboratorTests(APITestCase):

    def setUp(self):
        # Kreiraj korisnike sa jedinstvenim emailovima
        self.owner = User.objects.create_user(
            username="owner",
            password="pass",
            email="owner@example.com"
        )
        self.user = User.objects.create_user(
            username="collab",
            password="pass",
            email="collab@example.com"
        )

        # Kreiraj repo
        self.repo = Repository.objects.create(
            name="repo",
            visibility="public",
            owner=self.owner
        )

        # Generiši JWT token za owner-a
        refresh = RefreshToken.for_user(self.owner)
        self.access_token = str(refresh.access_token)

        # Postavi token u header klijenta
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_add_collaborator(self):
        response = self.client.post(
            f"/api/repositories/{self.repo.id}/collaborators/",
            {"user_id": self.user.id}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            RepositoryCollaborator.objects.filter(user=self.user).exists()
        )

    def test_list_collaborators(self):
        RepositoryCollaborator.objects.create(repository=self.repo, user=self.user)

        response = self.client.get(f"/api/repositories/{self.repo.id}/collaborators/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
    
    def test_add_collaborator_non_owner_forbidden(self):
        # običan korisnik koji nije owner
        user2 = User.objects.create_user(username="user2", email="user2@example.com", password="pass")
        refresh = RefreshToken.for_user(user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        response = self.client.post(
            f"/api/repositories/{self.repo.id}/collaborators/",
            {"user_id": self.user.id}
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_collaborator(self):
        RepositoryCollaborator.objects.create(repository=self.repo, user=self.user)
        response = self.client.delete(f"/api/repositories/{self.repo.id}/collaborators/{self.user.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            RepositoryCollaborator.objects.filter(user=self.user, repository=self.repo).exists()
        )

    def test_delete_non_owner_forbidden(self):
        RepositoryCollaborator.objects.create(repository=self.repo, user=self.user)
        # token običnog korisnika
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = self.client.delete(f"/api/repositories/{self.repo.id}/collaborators/{self.user.id}/")
        self.assertEqual(response.status_code, 403)

    def test_get_no_collaborators(self):
        response = self.client.get(f"/api/repositories/{self.repo.id}/collaborators/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_add_invalid_user_id(self):
        response = self.client.post(
            f"/api/repositories/{self.repo.id}/collaborators/",
            {"user_id": 99999}
        )
        self.assertEqual(response.status_code, 404)  # ili 400 ako view doda proveru