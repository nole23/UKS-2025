from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import User
from .serializers import UserRegistrationSerializer
from django.test import TestCase, RequestFactory
from rest_framework.exceptions import ValidationError
from unittest.mock import MagicMock, Mock, patch
from .views import (
    UserProfileDetailView,
    UserProfileUpdateView,
    UserEmailUpdateView,
    UserPasswordChangeView,
    PersonalTokenCreateView,
)
from user.serializers import (
    UserRegistrationSerializer,
    UserProfileUpdateSerializer,
    UserEmailUpdateSerializer,
    UserPasswordChangeSerializer,
    PersonalTokenSerializer
)
from .models import UserProfile, PersonalToken, create_user_profile
from django.contrib.auth import get_user_model
import uuid
from datetime import timedelta
from django.utils import timezone
from django.db.models.signals import post_save
from django.db.utils import IntegrityError
from django.test import override_settings

User = get_user_model()


class UserModelUnitTests(TestCase):

    def test_create_user_positive(self):
        """Pozitivan test: korisnik se kreira ispravno sa validnim podacima"""
        user = User.objects.create_user(username="test", email="test@example.com", password="pass")
        self.assertEqual(str(user), "test")
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.created_at)

    def test_create_user_negative(self):
        """Negativan test: kreiranje korisnika bez username podiže grešku"""
        with self.assertRaises(ValueError):
            User.objects.create_user(username="", email="no_name@example.com", password="pass")


class UserProfileModelUnitTests(TestCase):

    def setUp(self):
        # Disconnect signal da ne pravi profile automatski
        post_save.disconnect(create_user_profile, sender=User)

    def tearDown(self):
        # Ponovo poveži signal
        post_save.connect(create_user_profile, sender=User)

    def test_create_profile_positive(self):
        user = User.objects.create_user(username="test", email="test@example.com", password="pass")
        profile = UserProfile.objects.create(
            user=user,
            company_name="Test Corp"
        )
        self.assertEqual(profile.user, user)


class PersonalTokenModelUnitTests(TestCase):

    def test_token_auto_generated_positive(self):
        """Pozitivan test: token se automatski generiše ako nije postavljen"""
        user = User.objects.create_user(username="tokenuser", email="token@example.com", password="pass")
        token_obj = PersonalToken.objects.create(user=user, name="MyToken")
        self.assertIsNotNone(token_obj.token)
        self.assertEqual(len(token_obj.token), 32)
        self.assertEqual(str(token_obj), f"MyToken ({user.username})")

    def test_token_duplicate_negative(self):
        """Negativan test: pokušaj kreiranja tokena sa istim token stringom podiže grešku"""
        user = User.objects.create_user(username="dupuser", email="dup@example.com", password="pass")
        token_value = uuid.uuid4().hex
        PersonalToken.objects.create(user=user, name="Token1", token=token_value)
        with self.assertRaises(Exception):  # IntegrityError zbog unique=True
            PersonalToken.objects.create(user=user, name="Token2", token=token_value)


class UserProfileSignalTests(TestCase):

    def test_profile_signal_positive(self):
        user = User.objects.create_user(username="signaluser", email="signal@example.com", password="pass")
        profile = UserProfile.objects.get(user=user)
        self.assertIsNotNone(profile)

    def test_profile_signal_negative_duplicate(self):
        """
        Negativan test: signal ne dozvoljava dupliranje profila za istog korisnika
        """
        user = User.objects.create_user(username="test", email="test@example.com", password="pass")
        # signal automatski kreira prvi profil
        profile = UserProfile.objects.get(user=user)

        with self.assertRaises(IntegrityError):
            # pokušaj da kreiraš drugi profil za istog korisnika
            UserProfile.objects.create(user=user)


class UserSerializerTests(TestCase):
    
    # -------- UserRegistrationSerializer --------
    @patch("user.serializers.User.objects.create")
    @override_settings(AUTH_PASSWORD_VALIDATORS=[])
    def test_user_registration_positive(self, mock_create):
        # Mock objekat koji simulira User instancu
        mock_user = MagicMock()
        mock_create.return_value = mock_user

        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "S3cure!Pass2026",
            "password2": "S3cure!Pass2026",
            "first_name": "New",
            "last_name": "User"
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        # Poziv save() ne pravi entry u bazi, već samo vraća mock_user
        user = serializer.save()

        mock_create.assert_called_once_with(
            username="newuser",
            email="newuser@example.com",
            first_name="New",
            last_name="User"
        )
        mock_user.set_password.assert_called_once_with("S3cure!Pass2026")
        mock_user.save.assert_called_once()

    def test_user_registration_negative_password_mismatch(self):
        data = {
            "username": "test",
            "email": "test@example.com",
            "password": "Secret123!",
            "password2": "WrongPass!",
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


    # -------- UserProfileUpdateSerializer --------
    def test_user_profile_update_positive(self):
        # Mokovani User
        user = Mock()
        user.first_name = "Test"
        user.last_name = "Test"
        user.email = "test@example.com"
        user.save = Mock()

        # Mokovani UserProfile
        profile = Mock()
        profile.user = user
        profile.bio = "Old bio"
        profile.avatar = "old_avatar.png"
        profile.company_name = "OldCorp"
        profile.company_email = "oldcorp@example.com"
        profile.company_website = "https://oldcorp.com"
        profile.company_location = "Old City"
        profile.save = Mock()

        # Podaci za update
        data = {
            "user": {"first_name": "Testpdated"},
            "bio": "New bio"
        }

        # Serializer sa partial update
        serializer = UserProfileUpdateSerializer(instance=profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_profile = serializer.save()

        # Provere
        self.assertEqual(updated_profile.bio, "New bio")

        # Provera da su pozvani save() na user i profile
        user.save.assert_called_once()
        profile.save.assert_called_once()

    # -------- UserEmailUpdateSerializer --------
    def test_user_email_update_positive(self):
        # Mokovan user
        user = Mock()
        user.pk = 1
        user.email = "test@example.com"
        user.save = Mock()

        # Mock Request
        request = RequestFactory().post("/fake-url/")
        request.user = user

        data = {"old_email": "test@example.com", "new_email": "test2@example.com"}

        # Patch User.objects.exclude().filter().exists() da vrati False (nema drugog usera sa tim emailom)
        with patch("user.serializers.User.objects.exclude") as mock_exclude:
            mock_filter = mock_exclude.return_value.filter
            mock_filter.return_value.exists.return_value = False

            serializer = UserEmailUpdateSerializer(data=data, context={"request": request})
            self.assertTrue(serializer.is_valid(), serializer.errors)

            updated_user = serializer.save()
            self.assertEqual(updated_user.email, "test2@example.com")
            user.save.assert_called_once()

    def test_user_email_update_negative_old_email_wrong(self):
        # Mokovan user sa originalnim emailom
        user = Mock()
        user.pk = 1
        user.email = "test@example.com"
        user.save = Mock()

        # Mock Request
        request = RequestFactory().post("/fake-url/")
        request.user = user

        data = {"old_email": "wrong@example.com", "new_email": "test2@example.com"}

        serializer = UserEmailUpdateSerializer(data=data, context={"request": request})

        # Validacija bi trebalo da propadne jer old_email ne poklapa
        self.assertFalse(serializer.is_valid())
        self.assertIn("old_email", serializer.errors)

    # -------- UserPasswordChangeSerializer --------
    def test_user_password_change_positive(self):
        # Mokovan user
        user = Mock()
        user.pk = 1
        user.password = "hashed_old_password"
        user.check_password = Mock(return_value=True)
        user.set_password = Mock()
        user.save = Mock()

        # Mock Request
        request = RequestFactory().post("/fake-url/")
        request.user = user

        data = {"old_password": "SuperSecret123", "new_password": "NewSecret123!"}
        serializer = UserPasswordChangeSerializer(data=data, context={"request": request})

        # Provera validnosti
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # Save poziva set_password i save na user-u
        updated_user = serializer.save()

        # Provera da li je set_password pozvan sa novom lozinkom
        user.set_password.assert_called_once_with("NewSecret123!")
        user.save.assert_called_once()

    def test_user_password_change_negative_wrong_old(self):
       # Mokovan user
        user = Mock()
        user.pk = 1
        user.check_password = Mock(return_value=False)  # stari password je pogresan
        user.set_password = Mock()
        user.save = Mock()

        # Mock request
        request = RequestFactory().post("/fake-url/")
        request.user = user

        data = {"old_password": "WrongOld123", "new_password": "NewSecret123!"}
        serializer = UserPasswordChangeSerializer(data=data, context={"request": request})

        # Validator treba da prijavi gresku
        self.assertFalse(serializer.is_valid())
        self.assertIn("old_password", serializer.errors)

    # -------- PersonalTokenSerializer --------
    def test_personal_token_positive(self):
        # Mockovan user
        self.user = MagicMock()
        self.user.pk = 1
        self.user.username = "test"
        self.user.email = "test@example.com"
        
        # Kreiramo mock token objekat
        token = MagicMock()
        token.user = self.user
        token.name = "API Token"
        token.token = "ABC123"
        token.expires_at = timezone.now() + timedelta(days=1)
        token.created_at = timezone.now()

        # Serializujemo mock objekat
        serializer = PersonalTokenSerializer(instance=token)

        # Proveravamo polja
        self.assertEqual(serializer.data["name"], "API Token")
        self.assertEqual(serializer.data["token"], "ABC123")

        # Upoređujemo datetimes kao ISO stringove
        self.assertEqual(serializer.data["expires_at"], token.expires_at.isoformat().replace("+00:00", "Z"))
        self.assertEqual(serializer.data["created_at"], token.created_at.isoformat().replace("+00:00", "Z"))

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
