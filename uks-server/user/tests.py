from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from user.models import User
from user.serializers import UserRegistrationSerializer
from django.test import TestCase
from rest_framework.exceptions import ValidationError


class UserAuthTests(APITestCase):

    def setUp(self):
        # Kreiraćemo jednog korisnika za login test
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@email.com",
            password="testpass123"
        )
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')

    # -------------------
    # Registration tests
    # -------------------

    def test_register_user_positive(self):
        """Pozitivan test registracije novog korisnika"""
        data = {
            "username": "newuser",
            "email": "newuser@email.com",
            "password": "newpass123",
            "password2": "newpass123",
            "first_name": "New",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "newuser")

    def test_register_user_negative_password_mismatch(self):
        """Negativan test: lozinke se ne poklapaju"""
        data = {
            "username": "baduser",
            "email": "baduser@email.com",
            "password": "pass123",
            "password2": "pass456",
            "first_name": "Bad",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    # -------------
    # Login tests
    # -------------

    def test_login_user_positive(self):
        """Pozitivan test login-a sa validnim korisnikom"""
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_user_negative_wrong_password(self):
        """Negativan test login-a sa pogresnom lozinkom"""
        data = {
            "username": "testuser",
            "password": "wrongpass"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)


class UserRegistrationSerializerTest(TestCase):

    def test_serializer_valid_data_positive(self):
        """Serializer kreira korisnika sa validnim podacima"""
        data = {
            "username": "newuser",
            "email": "newuser@email.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "first_name": "New",
            "last_name": "User"
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "newuser@email.com")
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "User")

    def test_serializer_password_mismatch_negative(self):
        """Serializer vraća grešku ako se password i password2 ne poklapaju"""
        data = {
            "username": "baduser",
            "email": "baduser@email.com",
            "password": "pass123",
            "password2": "pass456",
            "first_name": "Bad",
            "last_name": "User"
        }
        serializer = UserRegistrationSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("password", context.exception.detail)
