from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class DockerInfoViewTests(APITestCase):

    def setUp(self):
        # Kreiraj test korisnika
        self.user = User.objects.create_user(username="testuser", password="pass")

        # Generiši JWT token za korisnika
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_info(self):
        # Dodaj token u header
        response = self.client.get(
            "/api/docker/info", 
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("application", response.data)
        self.assertEqual(response.data["application"], "DockerHub Clone")
    
    def test_unauthenticated_access(self):
        response = self.client.get("/api/docker/info")
        self.assertEqual(response.status_code, 401)

    def test_response_fields(self):
        response = self.client.get(
            "/api/docker/info", 
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("description", response.data)
        self.assertEqual(response.data["description"], "Platform for managing container repositories")
        self.assertIn("features", response.data)
        self.assertListEqual(
            response.data["features"],
            ["Repositories", "Organizations", "Tags", "Pulls", "Stars"]
        )

    def test_invalid_methods(self):
        for method in ["post", "put", "delete", "patch"]:
            client_method = getattr(self.client, method)
            response = client_method("/api/docker/info", HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
            self.assertEqual(response.status_code, 405)