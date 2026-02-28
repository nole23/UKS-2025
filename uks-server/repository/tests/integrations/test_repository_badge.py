from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from repository.models import Repository
from django.contrib.auth.models import Group

User = get_user_model()


class RepositoryBadgeUpdateTests(APITestCase):

    def setUp(self):
        # 1. Kreiraj korisnika
        self.superuser = User.objects.create_user(username="admin", password="pass")

        # 2. Dodaj korisnika u Superadmin grupu
        group, _ = Group.objects.get_or_create(name="Superadmin")
        self.superuser.groups.add(group)
        self.superuser.save()

        # 3. Kreiraj repo sa owner = superuser
        self.repo = Repository.objects.create(
            name="repo",
            visibility="public",
            owner=self.superuser
        )

        # 4. JWT token
        refresh = RefreshToken.for_user(self.superuser)
        self.access_token = str(refresh.access_token)

        # 5. PATCH request
        response = self.client.patch(
            f"/api/repositories/{self.repo.id}/badge/",
            {"badge": "VERIFIED"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

    def test_update_badge(self):
        # Pošalji PATCH sa JWT tokenom
        response = self.client.patch(
            f"/api/repositories/{self.repo.id}/badge/",
            {"badge": "VERIFIED"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 200)
        self.repo.refresh_from_db()
        self.assertEqual(self.repo.badge, "VERIFIED")
    
    def test_non_superadmin_cannot_set_official(self):
        # Kreiraj običnog korisnika i repo koji je u njegovom vlasništvu
        user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass"
        )
        repo = Repository.objects.create(name="repo2", owner=user)
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)

        response = self.client.patch(
            f"/api/repositories/{repo.id}/badge/",
            {"badge": "OFFICIAL"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )
        self.assertEqual(response.status_code, 403)

    def test_invalid_badge_value(self):
        response = self.client.patch(
            f"/api/repositories/{self.repo.id}/badge/",
            {"badge": "INVALID"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid badge", response.data["error"])

    def test_patch_nonexistent_repo(self):
        response = self.client.patch(
            f"/api/repositories/9999/badge/",
            {"badge": "VERIFIED"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Repository not found", response.data["error"])

    def test_unauthenticated_access(self):
        response = self.client.patch(
            f"/api/repositories/{self.repo.id}/badge/",
            {"badge": "VERIFIED"},
            format="json"
        )
        self.assertEqual(response.status_code, 401)