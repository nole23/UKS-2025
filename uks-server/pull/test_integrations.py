from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from repository.models import Repository
from pull.models import Pull
from user.models import User  # prilagodi import ako je User model negde drugo


class PullRepositoryViewIntegrationTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "strongpass123",
            "password2": "strongpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        login_data = {"username": "testuser", "password": "strongpass123"}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.user = User.objects.get(username="testuser")
        self.repo = Repository.objects.create(name="TestRepo", visibility="public", owner=self.user)
        self.pull_url = reverse('repository-pull', kwargs={"pk": self.repo.id})
        self.pulls_url = reverse('repository-pulls', kwargs={"pk": self.repo.id})

    def test_post_pull_repository(self):
        response = self.client.post(self.pull_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"message": "Pulled successfully"})

        self.repo.refresh_from_db()
        self.assertEqual(self.repo.pulls_count, 2)
        self.assertEqual(Pull.objects.filter(repository=self.repo).count(), 1)

    def test_get_pulls_list(self):
        Pull.objects.create(repository=self.repo)
        Pull.objects.create(repository=self.repo)

        response = self.client.get(self.pulls_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn("id", response.data[0])
        self.assertIn("pulled_at", response.data[0])

    def test_post_pull_repository_not_found(self):
        url = reverse('repository-pull', kwargs={"pk": 999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"error": "Repository not found"})
