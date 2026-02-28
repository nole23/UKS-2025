# star/tests_integration.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from user.models import User
from repository.models import Repository
from star.models import Star

class StarRepositoryIntegrationTests(APITestCase):

    def setUp(self):
        # ----------------------
        # URL-ovi
        # ----------------------
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.starred_url = reverse('starred-repositories') if 'starred-repositories' in [u.name for u in []] else "/api/repositories/starred/"

        # ----------------------
        # Kreiranje i registracija korisnika
        # ----------------------
        self.user_data = {
            "username": "staruser",
            "email": "staruser@example.com",
            "password": "strongpass123",
            "password2": "strongpass123",
            "first_name": "Star",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # ----------------------
        # Login i čuvanje JWT tokena
        # ----------------------
        login_data = {"username": "staruser", "password": "strongpass123"}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # ----------------------
        # Kreiranje test repozitorijuma
        # ----------------------
        self.user = User.objects.get(username="staruser")
        self.repo_public = Repository.objects.create(
            name="PublicRepo", visibility="public", owner=self.user
        )
        self.repo_private = Repository.objects.create(
            name="PrivateRepo", visibility="private", owner=self.user
        )

    # ----------------------
    # POST /star/ - dodavanje star
    # ----------------------
    def test_star_repository(self):
        url = f"/api/repositories/{self.repo_public.id}/star/"
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Starred")

        # Proveri da li je u bazi
        star_exists = Star.objects.filter(user=self.user, repository=self.repo_public).exists()
        self.assertTrue(star_exists)

        # Proveri da li je povećan stars_count
        self.repo_public.refresh_from_db()
        self.assertEqual(self.repo_public.stars_count, 2)

    # ----------------------
    # DELETE /star/ - uklanjanje star
    # ----------------------
    def test_unstar_repository(self):
        # Prvo dodamo star
        Star.objects.create(user=self.user, repository=self.repo_public)
        self.repo_public.stars_count = 1
        self.repo_public.save()

        url = f"/api/repositories/{self.repo_public.id}/star/"
        response = self.client.delete(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Unstarred")

        # Proveri da li je izbrisano iz baze
        star_exists = Star.objects.filter(user=self.user, repository=self.repo_public).exists()
        self.assertFalse(star_exists)

        # Proveri da li je smanjen stars_count
        self.repo_public.refresh_from_db()
        self.assertEqual(self.repo_public.stars_count, 0)

    # ----------------------
    # GET /starred/ - dohvatanje svih starovanih repozitorijuma
    # ----------------------
    def test_get_starred_repositories(self):
        # Dodajemo par star-ova
        Star.objects.create(user=self.user, repository=self.repo_public)
        Star.objects.create(user=self.user, repository=self.repo_private)

        url = "/api/repositories/starred/"
        response = self.client.get(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        repo_names = [r['name'] for r in response.data]
        self.assertIn("PublicRepo", repo_names)
        self.assertIn("PrivateRepo", repo_names)
