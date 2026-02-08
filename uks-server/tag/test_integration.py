# tag/tests_integration.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from user.models import User
from repository.models import Repository
from tag.models import Tag

class RepositoryTagIntegrationTests(APITestCase):

    def setUp(self):
        # ----------------------
        # URL-ovi
        # ----------------------
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')

        # ----------------------
        # Kreiranje i registracija korisnika
        # ----------------------
        self.user_data = {
            "username": "taguser",
            "email": "taguser@example.com",
            "password": "strongpass123",
            "password2": "strongpass123",
            "first_name": "Tag",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # ----------------------
        # Login i čuvanje JWT tokena
        # ----------------------
        login_data = {"username": "taguser", "password": "strongpass123"}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # ----------------------
        # Kreiranje test repozitorijuma
        # ----------------------
        self.user = User.objects.get(username="taguser")
        self.repo = Repository.objects.create(
            name="RepoWithTags", visibility="public", owner=self.user
        )

    # ----------------------
    # GET /tags/ - dohvatanje tagova
    # ----------------------
    def test_get_tags_empty(self):
        url = f"/api/repositories/{self.repo.id}/tags/"
        response = self.client.get(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_tags_with_data(self):
        # Kreiramo tagove
        tag1 = Tag.objects.create(
            repository=self.repo, name="v1.0", digest="sha256:aaa", compressed_size_mb=50, os_arch="linux/amd64"
        )
        tag2 = Tag.objects.create(
            repository=self.repo, name="v1.1", digest="sha256:bbb", compressed_size_mb=55, os_arch="linux/amd64"
        )

        url = f"/api/repositories/{self.repo.id}/tags/"
        response = self.client.get(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        names = [t['name'] for t in response.data]
        self.assertIn("v1.0", names)
        self.assertIn("v1.1", names)

    # ----------------------
    # POST /tags/ - dodavanje novog taga
    # ----------------------
    def test_post_create_tag(self):
        url = f"/api/repositories/{self.repo.id}/tags/"
        data = {
            "name": "latest",
            "digest": "sha256:abcd1234",
            "compressed_size_mb": 100,
            "os_arch": "linux/amd64"
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "latest")

        # Proveri bazu
        tag = Tag.objects.get(id=response.data['id'])
        self.assertEqual(tag.repository, self.repo)
        self.assertEqual(tag.digest, "sha256:abcd1234")

        # Proveri da li je updated last_pushed_at repoa
        self.repo.refresh_from_db()
        self.assertIsNotNone(self.repo.last_pushed_at)

    # ----------------------
    # DELETE non-existent tag - negativan test
    # ----------------------
    def test_delete_tag_not_found(self):
        url = f"/api/repositories/{self.repo.id}/tags/999/"
        response = self.client.delete(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Tag not found")
