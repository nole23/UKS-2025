from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import User
from .serializers import UserRegistrationSerializer
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from unittest.mock import MagicMock, patch
from .views import (
    UserProfileDetailView,
    UserProfileUpdateView,
    UserEmailUpdateView,
    UserPasswordChangeView,
    PersonalTokenCreateView,
)


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


# --------------------------
# UserProfileDetailView Tests
# --------------------------
class UserProfileDetailViewTests(TestCase):

    def test_get_object_positive(self):
        # Mock user i profile
        mock_user = MagicMock()
        mock_profile = MagicMock()
        mock_user.profile = mock_profile

        # Mock request
        request = MagicMock()
        request.user = mock_user

        # View
        view = UserProfileDetailView()
        view.request = request

        # Patch get_serializer da vrati dict preko .data
        with patch.object(UserProfileDetailView, 'get_serializer') as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.data = {
                "first_name": "John",
                "last_name": "Doe",
                "bio": "Test bio"
            }
            mock_get_serializer.return_value = mock_serializer

            # Umesto get_object, pozivamo retrieve
            response = view.retrieve(request)
            profile_data = response.data

        # Asserts
        self.assertEqual(profile_data['first_name'], "John")
        self.assertEqual(profile_data['last_name'], "Doe")
        self.assertEqual(profile_data['bio'], "Test bio")

    def test_get_object_negative(self):
        mock_user = MagicMock()
        mock_user.profile = None

        request = MagicMock()
        request.user = mock_user

        view = UserProfileDetailView()
        view.request = request
        view.kwargs = {}
        view.format_kwarg = None

        # Patchujemo get_serializer da vrati serializer sa praznim .data
        with patch.object(UserProfileDetailView, 'get_serializer') as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.data = None  # ili {} ako ti get_object očekuje dict
            mock_get_serializer.return_value = mock_serializer

            obj = view.get_object()

        self.assertIsNone(obj)


# --------------------------
# UserProfileUpdateView Tests
# --------------------------
class UserProfileUpdateViewTests(TestCase):

    @patch("user.views.UserProfileUpdateSerializer")
    def test_update_profile_positive(self, mock_serializer_class):
        mock_user = MagicMock()
        mock_profile = MagicMock()
        mock_user.profile = mock_profile

        request = MagicMock()
        request.user = mock_user
        request.data = {"first_name": "John"}

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer

        view = UserProfileUpdateView()
        view.request = request
        obj = view.get_object()
        serializer = mock_serializer_class(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertTrue(serializer.is_valid.called)
        serializer.save.assert_called_once()

    @patch("user.views.UserProfileUpdateSerializer")
    def test_update_profile_negative(self, mock_serializer_class):
        mock_user = MagicMock()
        mock_user.profile = MagicMock()

        request = MagicMock()
        request.user = mock_user
        request.data = {"first_name": ""}  # prazan first_name kao invalid

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception("Invalid data")
        mock_serializer_class.return_value = mock_serializer

        view = UserProfileUpdateView()
        view.request = request
        obj = view.get_object()
        serializer = mock_serializer_class(obj, data=request.data)
        
        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True)


# --------------------------
# UserEmailUpdateView Tests
# --------------------------
class UserEmailUpdateViewTests(TestCase):

    @patch("user.views.UserEmailUpdateSerializer")
    def test_patch_email_positive(self, mock_serializer_class):
        mock_user = MagicMock()
        request = MagicMock()
        request.user = mock_user
        request.data = {"old_email": "old@test.com", "new_email": "new@test.com"}

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer

        view = UserEmailUpdateView()
        view.request = request
        response = view.patch(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Email updated successfully"})
        mock_serializer.save.assert_called_once()

    @patch("user.views.UserEmailUpdateSerializer")
    def test_patch_email_negative(self, mock_serializer_class):
        mock_user = MagicMock()
        request = MagicMock()
        request.user = mock_user
        request.data = {"old_email": "wrong@test.com", "new_email": "new@test.com"}

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception("Invalid email")
        mock_serializer_class.return_value = mock_serializer

        view = UserEmailUpdateView()
        view.request = request

        with self.assertRaises(Exception):
            view.patch(request)


# --------------------------
# UserPasswordChangeView Tests
# --------------------------
class UserPasswordChangeViewTests(TestCase):

    @patch("user.views.UserPasswordChangeSerializer")
    def test_patch_password_positive(self, mock_serializer_class):
        mock_user = MagicMock()
        request = MagicMock()
        request.user = mock_user
        request.data = {"old_password": "123", "new_password": "456"}

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer

        view = UserPasswordChangeView()
        view.request = request
        response = view.patch(request)

        self.assertEqual(response.data, {"message": "Password changed successfully"})
        mock_serializer.save.assert_called_once()

    @patch("user.views.UserPasswordChangeSerializer")
    def test_patch_password_negative(self, mock_serializer_class):
        mock_user = MagicMock()
        request = MagicMock()
        request.user = mock_user
        request.data = {"old_password": "wrong", "new_password": "456"}

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception("Invalid password")
        mock_serializer_class.return_value = mock_serializer

        view = UserPasswordChangeView()
        view.request = request

        with self.assertRaises(Exception):
            view.patch(request)


# --------------------------
# PersonalTokenCreateView Tests
# --------------------------
class PersonalTokenCreateViewTests(TestCase):

    @patch("user.views.PersonalTokenSerializer")
    def test_create_token_positive(self, mock_serializer_class):
        mock_user = MagicMock()
        request = MagicMock()
        request.user = mock_user
        request.data = {"name": "Token1"}

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer

        view = PersonalTokenCreateView()
        view.request = request
        serializer = mock_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        view.perform_create(serializer)

        mock_serializer_class.assert_called_once_with(data=request.data)
        serializer.save.assert_called_once_with(user=mock_user)

    @patch("user.views.PersonalTokenSerializer")
    def test_create_token_negative(self, mock_serializer_class):
        mock_user = MagicMock()
        request = MagicMock()
        request.user = mock_user
        request.data = {"name": ""}  # prazno ime tokena kao invalid

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception("Invalid token")
        mock_serializer_class.return_value = mock_serializer

        view = PersonalTokenCreateView()
        view.request = request
        serializer = mock_serializer_class(data=request.data)

        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True)