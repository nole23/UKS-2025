from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.cache import cache
from django.contrib.auth.models import Group

from repository.models import Repository
from star.models import Star  # obavezno da je ovde Star
from user.models import User  # ili User model koji koristiš

class StarRepositoryIntegrationTests(APITestCase):
    def setUp(self):
        # svaki korisnik mora imati jedinstveni email
        self.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="pass"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@example.com", password="pass"
        )
        self.superadmin = User.objects.create_user(
            username="admin", email="admin@example.com", password="pass"
        )
        superadmin_group, _ = Group.objects.get_or_create(name="Superadmin")
        self.superadmin.groups.add(superadmin_group)

        # repo
        self.repo = Repository.objects.create(name="TestRepo", owner=self.owner, stars_count=0)

        # API client
        self.client = APIClient()

        # login owner-a za test POST/DELETE
        self.client.force_authenticate(user=self.owner)

    def test_get_repo_not_exist(self):
        url = reverse("star-repository", kwargs={"pk": 9999})
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_permission_denied(self):
        url = reverse("star-repository", kwargs={"pk": self.repo.pk})
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_owner_success_and_cache(self):
        url = reverse("star-repository", kwargs={"pk": self.repo.pk})
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        # keširanje
        cache_key = f"repo_stars_{self.repo.pk}"
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data, [])

    def test_post_and_delete_star(self):
        # --- POST (starring) ---
        post_url = f"/api/repositories/{self.repo.pk}/star/"
        post_response = self.client.post(post_url)
        self.assertEqual(post_response.status_code, 200)
        self.assertEqual(post_response.data, {"message": "Starred"})

        # Proveri da li je Star objekat kreiran
        star_obj = Star.objects.filter(user=self.owner, repository=self.repo).first()
        self.assertIsNotNone(star_obj)

        # Proveri da li je stars_count povećan
        self.repo.refresh_from_db()
        self.assertEqual(self.repo.stars_count, 2)

        # --- DELETE (unstarring) ---
        delete_response = self.client.delete(post_url)
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.data, {"message": "Unstarred"})

        # Proveri da li je Star objekat obrisan
        star_obj = Star.objects.filter(user=self.owner, repository=self.repo).first()
        self.assertIsNone(star_obj)

        # Proveri da li je stars_count smanjen
        self.repo.refresh_from_db()
        self.assertEqual(self.repo.stars_count, 1)

    def tearDown(self):
        cache.clear()