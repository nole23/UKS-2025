from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from user.models import User

class UserViewsIntegrationTest(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')

    # -------------------
    # Registration tests
    # -------------------

    def test_register_user_integration(self):
        """Integracioni test registracije korisnika"""
        data = {
            "username": "intuser",
            "email": "intuser@email.com",
            "password": "Integration123!",
            "password2": "Integration123!",
            "first_name": "Int",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, data, format='json')

        # Proveravamo da li je status 201 CREATED
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Proveravamo da li je korisnik stvarno u bazi
        user = User.objects.get(username="intuser")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "intuser@email.com")
        self.assertTrue(user.check_password("Integration123!"))

        # Proveravamo odgovor JSON-a
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "intuser")
        self.assertEqual(response.data["user"]["email"], "intuser@email.com")
        self.assertIn("message", response.data)

    def test_register_user_integration_password_mismatch(self):
        """Negativan integracioni test: lozinke se ne poklapaju"""
        data = {
            "username": "badintuser",
            "email": "badintuser@email.com",
            "password": "Password1",
            "password2": "Password2",
            "first_name": "Bad",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    # -------------
    # Login tests
    # -------------

    def test_login_user_integration(self):
        """Integracioni test login-a"""
        # Prvo kreiramo korisnika
        user = User.objects.create_user(
            username="loginuser",
            email="loginuser@email.com",
            password="Login123!"
        )

        data = {
            "username": "loginuser",
            "password": "Login123!"
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_user_wrong_password_integration(self):
        """Negativan test login-a sa pogresnom lozinkom"""
        user = User.objects.create_user(
            username="loginuser2",
            email="loginuser2@email.com",
            password="CorrectPass123"
        )

        data = {
            "username": "loginuser2",
            "password": "WrongPass"
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
