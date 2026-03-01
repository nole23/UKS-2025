from django.test import TestCase
from django.core.cache import cache
from rest_framework.test import APIClient
from repository.models import Repository
from star.models import Star
from django.contrib.auth import get_user_model

User = get_user_model()

class StarredRepositoriesViewIntegrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

        # korisnici
        self.user_with_stars = User.objects.create_user(username="star_user", email="star@example.com", password="pass")
        self.user_without_stars = User.objects.create_user(username="no_star_user", email="no_star@example.com", password="pass")

        # repozitorijumi
        self.repo1 = Repository.objects.create(name="Repo1", owner=self.user_with_stars)
        self.repo2 = Repository.objects.create(name="Repo2", owner=self.user_without_stars)

        # dodaj star
        Star.objects.create(user=self.user_with_stars, repository=self.repo1)

    def test_get_starred_repositories_with_results_and_cache(self):
        self.client.force_authenticate(user=self.user_with_stars)
        url = "/api/repositories/starred/"
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.repo1.id)

        # proveri cache
        cached_data = cache.get(f"repositori_view_{self.user_with_stars}")
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data[0]['id'], self.repo1.id)

    def test_get_starred_repositories_empty(self):
        self.client.force_authenticate(user=self.user_without_stars)
        url = "/api/repositories/starred/"
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        # cache bi trebao biti setovan i prazan
        cached_data = cache.get(f"repositori_view_{self.user_without_stars}")
        self.assertIsNotNone(cached_data)
        self.assertEqual(len(cached_data), 0)

    def test_unauthenticated_user_cannot_access(self):
        url = "/api/repositories/starred/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)