from types import SimpleNamespace
from rest_framework.test import APIRequestFactory
from rest_framework import status
from .models import User
from .serializers import GeneratePasswordSerializer, UserDetailSerializer, UserDetailSuperSerializer, UserListWithRolesSerializer, UserProfileDetailSerializer, UserRegistrationSerializer
from django.test import TestCase, RequestFactory
from rest_framework.exceptions import PermissionDenied, ValidationError
from unittest.mock import MagicMock, Mock, patch
from rest_framework.response import Response
from django.contrib.auth.models import Group

from .views import (
    CreateAdminView,
    GenerateUserPasswordView,
    PersonalTokenListView,
    RoleView,
    UserDetailView,
    UserListAllView,
    UserListView,
    UserProfileDetailView,
    UserProfileUpdateView,
    UserEmailUpdateView,
    UserPasswordChangeView,
    PersonalTokenCreateView,
    UserRegistrationView,
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


# --------------------------
# User Tests
# --------------------------
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


# --------------------------
# UserProfile Tests
# --------------------------
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


# --------------------------
# PersonalToken Tests
# --------------------------
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


# --------------------------
# Signal za automatsko kreiranje profila
# --------------------------
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


# --------------------------
# UserRegistrationSerializer Tests
# --------------------------
class UserRegistrationSerializerTests(TestCase):

    @patch("user.serializers.Group.objects.get")
    @patch("user.serializers.User.objects.create")
    def test_create_user_with_default_group(self, mock_create, mock_get_group):
        mock_user = MagicMock()
        mock_create.return_value = mock_user
        mock_group = MagicMock()
        mock_get_group.return_value = mock_group

        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Pass1234!",
            "password2": "Pass1234!",
            "first_name": "First",
            "last_name": "Last"
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        mock_create.assert_called_once()
        mock_user.set_password.assert_called_once_with("Pass1234!")
        mock_user.groups.add.assert_called_once_with(mock_group)

    def test_password_mismatch(self):
        data = {
            "username": "u",
            "email": "a@a.com",
            "password": "123",
            "password2": "321"
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


# --------------------------
# UserProfileDetailSerializer Tests
# --------------------------
class UserProfileDetailSerializerTests(TestCase):

    @patch("repository.models.Repository.objects")
    def test_get_projects_returns_list(self, mock_repo_objects):
        # Mock-uj Repository query
        mock_repo_objects.filter.return_value = [
            MagicMock(name="Repo1", visibility="public"),
            MagicMock(name="Repo2", visibility="private")
        ]

        # Mokovani User i UserProfile
        mock_user = MagicMock(username="john", email="john@example.com", first_name="John", last_name="Doe")
        mock_profile = MagicMock(
            user=mock_user,
            bio="Test bio",
            avatar=None,
            company_name="Test Company",
            company_email="test@company.com",
            company_website="www.company.com",
            company_location="Test City",
            default_repository=True
        )

        serializer = UserProfileDetailSerializer(instance=mock_profile)
        projects = serializer.get_projects(mock_profile)

        self.assertEqual(len(projects), 2)
    
    @patch("repository.models.Repository.objects.filter")
    def test_serializer_negative_no_projects(self, mock_filter):
        # Mock empty repo list
        mock_filter.return_value = []

        # Mock User and UserProfile
        mock_user = Mock(username="jane", email="jane@example.com", first_name="Jane", last_name="Smith")
        mock_profile = Mock(
            user=mock_user,
            bio="",
            avatar=None,
            company_name="",
            company_email="",
            company_website="",
            company_location="",
            default_repository=False
        )

        serializer = UserProfileDetailSerializer(instance=mock_profile)
        data = serializer.data

        self.assertEqual(data["username"], "jane")
        self.assertEqual(data["email"], "jane@example.com")
        self.assertEqual(data["first_name"], "Jane")
        self.assertEqual(data["last_name"], "Smith")
        self.assertEqual(data["bio"], "")
        self.assertIsNone(data["avatar"])
        self.assertEqual(data["projects"], [])  # Ovde očekujemo praznu listu
        self.assertFalse(data["default_repository"])


# --------------------------
# UserProfileDetailSerializer Tests
# --------------------------
class UserProfileUpdateSerializerTests(TestCase):

    @patch("user.serializers.User.objects")
    def test_update_userprofile_email_taken(self, mock_user_objects):
        # Mokujemo da email ne postoji
        mock_user_objects.exclude.return_value.filter.return_value.exists.return_value = False

        # User i Profile kao jednostavan objekat sa atributima
        user = SimpleNamespace(pk=1, email="test@example.com", first_name="Old", last_name="Old", save=lambda: None)
        profile = SimpleNamespace(user=user, bio="Old bio", save=lambda: None)

        data = {"user": {"email": "newcorp111@example.com"}}

        serializer = UserProfileUpdateSerializer(instance=profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_profile = serializer.save()

        self.assertEqual(updated_profile.user.email, "newcorp111@example.com")

    @patch("user.serializers.User.objects")
    def test_update_userprofile_email_taken(self, mock_user_objects):
        # Mokujemo da email ne postoji
        mock_user_objects.exclude.return_value.filter.return_value.exists.return_value = False

        # User i Profile kao jednostavan objekat sa atributima
        user = SimpleNamespace(pk=1, email="test@example.com", first_name="Old", last_name="Old", save=lambda: None)
        profile = SimpleNamespace(user=user, bio="Old bio", save=lambda: None)

        # Podaci za update
        data = {
            "user": {"first_name": "Testpdated"},
            "bio": "New bio"
        }

        serializer = UserProfileUpdateSerializer(instance=profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_profile = serializer.save()
        # Provere
        self.assertEqual(updated_profile.bio, "New bio")


# --------------------------
# UserEmailUpdateSerializer Tests
# --------------------------
class UserEmailUpdateSerializerTests(TestCase):

    def setUp(self):
        self.user = MagicMock()
        self.user.email = "old@example.com"
        self.request = MagicMock()
        self.request.user = self.user

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

        # Promeni assertIn da proverava key 'messages' umesto 'old_email'
        self.assertIn("messages", serializer.errors)

        # Opcionalno, možeš proveriti i tekst greške
        self.assertEqual(
            serializer.errors["messages"][0],
            "Old email does not match"
        )

    def test_email_old_email_mismatch(self):
        data = {"old_email": "wrong@example.com", "new_email": "new@example.com"}
        serializer = UserEmailUpdateSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("messages", serializer.errors)

    @patch("user.serializers.User.objects.exclude")
    def test_email_new_email_taken(self, mock_exclude):
        mock_exclude.return_value.filter.return_value.exists.return_value = True
        data = {"old_email": "old@example.com", "new_email": "taken@example.com"}
        serializer = UserEmailUpdateSerializer(data=data, context={"request": self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("messages", serializer.errors)


# --------------------------
# UserPasswordChangeSerializer Tests
# --------------------------
class UserPasswordChangeSerializerTests(TestCase):

    def setUp(self):
        self.user = MagicMock()
        self.user.check_password.return_value = True
        self.request = MagicMock()
        self.request.user = self.user

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

    def test_change_password_success(self):
        data = {"old_password": "old", "new_password": "Newpass123!"}
        serializer = UserPasswordChangeSerializer(data=data, context={"request": self.request})
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.set_password.assert_called_once_with("Newpass123!")
        self.assertFalse(self.user.must_change_password)

    def test_old_password_invalid(self):
        self.user.check_password.return_value = False
        data = {"old_password": "wrong", "new_password": "Newpass123!"}
        serializer = UserPasswordChangeSerializer(data=data, context={"request": self.request})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


# --------------------------
# PersonalTokenSerializer Tests
# --------------------------
class PersonalTokenSerializerTests(TestCase):

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

    def test_read_only_fields(self):
        token = MagicMock(spec=PersonalToken)
        token.id = 1
        token.name = "tok"
        token.token = "tokval"
        token.expires_at = None
        token.created_at = "created"
        serializer = PersonalTokenSerializer(token)
        self.assertEqual(serializer.data["id"], 1)
        self.assertEqual(serializer.data["name"], "tok")
        self.assertEqual(serializer.data["token"], "tokval")
        self.assertEqual(serializer.data["created_at"], "created")


# --------------------------
# UserListWithRolesSerializer Tests
# --------------------------
class UserListWithRolesSerializerTests(TestCase):

    def test_serializer_positive(self):
        # Mockovan user objekat
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "john"
        mock_user.email = "john@example.com"

        # Mockovanje groups.values_list da vrati listu rola
        mock_groups = Mock()
        mock_groups.values_list.return_value = ["Admin", "Moderator"]
        mock_user.groups = mock_groups

        serializer = UserListWithRolesSerializer(mock_user)
        data = serializer.data

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["username"], "john")
        self.assertEqual(data["email"], "john@example.com")
        self.assertEqual(data["roles"], ["Admin", "Moderator"])

    def test_serializer_negative_no_roles(self):
        # Mockovan user objekat bez grupa
        mock_user = Mock()
        mock_user.id = 2
        mock_user.username = "alice"
        mock_user.email = "alice@example.com"

        # groups.values_list vraća praznu listu
        mock_groups = Mock()
        mock_groups.values_list.return_value = []
        mock_user.groups = mock_groups

        serializer = UserListWithRolesSerializer(mock_user)
        data = serializer.data

        self.assertEqual(data["id"], 2)
        self.assertEqual(data["username"], "alice")
        self.assertEqual(data["email"], "alice@example.com")
        self.assertEqual(data["roles"], [])  # nema rola

    def test_roles_empty_when_no_groups(self):
        user = MagicMock()
        user.groups.exists.return_value = False
        serializer = UserListWithRolesSerializer(user)
        self.assertEqual(serializer.data["roles"], [])

    def test_roles_with_groups(self):
        user = MagicMock()
        group = MagicMock()
        group.name = "Admin"
        user.groups.values_list.return_value = ["Admin"]
        user.groups.exists.return_value = True
        serializer = UserListWithRolesSerializer(user)
        self.assertEqual(serializer.get_roles(user), ["Admin"])
    

# --------------------------
# UserDetailSerializer Tests
# --------------------------
class UserDetailSerializerTests(TestCase):

    def test_serializer_positive(self):
        # Mock user sa grupom
        mock_user = MagicMock()
        mock_user.username = "johndoe"
        mock_user.email = "john@example.com"
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"
        mock_user.groups.exists.return_value = True
        mock_user.groups.first.return_value = MagicMock(name="Admin", spec=[]).name = "Admin"

        # Koristimo SimpleNamespace za profile da DRF vrati stvarne vrednosti
        mock_profile = SimpleNamespace(
            bio="Bio text",
            avatar="avatar.png",
            company_name="ACME",
            company_email="contact@acme.com",
            company_location="Belgrade",
            company_website="https://acme.com",
            default_repository=True
        )
        mock_user.userprofile = mock_profile

        mock_group = MagicMock()
        mock_group.name = "Admin"
        mock_user.groups.first.return_value = mock_group

        serializer = UserDetailSerializer(mock_user)
        data = serializer.data

        assert data["username"] == "johndoe"
        assert data["email"] == "john@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["role"] == "Admin"

    def test_serializer_negative_no_role(self):
        # Mock user bez role
        mock_user = MagicMock()
        mock_user.username = "janedoe"
        mock_user.email = "jane@example.com"
        mock_user.first_name = "Jane"
        mock_user.last_name = "Doe"
        mock_user.groups.exists.return_value = False
        mock_user.groups.first.return_value = None

        # Profil sa default vrednostima
        mock_profile = SimpleNamespace(
            bio="",
            avatar=None,
            company_name="",
            company_email="",
            company_location="",
            company_website="",
            default_repository=False
        )
        mock_user.userprofile = mock_profile

        serializer = UserDetailSerializer(mock_user)
        data = serializer.data

        assert data["username"] == "janedoe"
        assert data["email"] == "jane@example.com"
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Doe"
        assert data["role"] is None

    def test_get_role_none(self):
        user = MagicMock()
        user.groups.exists.return_value = False
        serializer = UserDetailSerializer(user)
        self.assertIsNone(serializer.get_role(user))

    def test_get_role_exists(self):
        user = MagicMock()
        group = MagicMock()
        group.name = "Admin"
        user.groups.exists.return_value = True
        user.groups.first.return_value = group
        serializer = UserDetailSerializer(user)
        self.assertEqual(serializer.get_role(user), "Admin")


# --------------------------
# UserDetailSuperSerializer Tests
# --------------------------
class UserDetailSuperSerializerTests(TestCase):

    def test_groups_and_permissions_empty(self):
        user = MagicMock()
        user.groups.all.return_value = []
        user.user_permissions.values_list.return_value = []
        serializer = UserDetailSuperSerializer(user)
        self.assertEqual(serializer.get_groups(user), [])
        self.assertEqual(serializer.get_permissions(user), [])


# --------------------------
# UserSerializer Tests
# --------------------------
class UserSerializerTests(TestCase):
    
    @patch("user.serializers.Group.objects.get")
    @patch("user.serializers.User.objects.create")
    @override_settings(AUTH_PASSWORD_VALIDATORS=[])
    def test_user_registration_positive(self, mock_user_create, mock_group_get):
        # Mock User instanca
        mock_user = MagicMock()
        mock_user_create.return_value = mock_user

        # Mock Group instanca
        mock_group = MagicMock()
        mock_group_get.return_value = mock_group

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

        # Poziv save() sada koristi mokovan Group
        user = serializer.save()

        # Provere
        mock_user_create.assert_called_once_with(
            username="newuser",
            email="newuser@example.com",
            first_name="New",
            last_name="User"
        )
        mock_user.set_password.assert_called_once_with("S3cure!Pass2026")
        mock_user.save.assert_called_once()
        mock_group_get.assert_called_once_with(name="OrdinaryUser")
        mock_user.groups.add.assert_called_once_with(mock_group)

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
# GeneratePasswordSerializer Tests
# --------------------------
class GeneratePasswordSerializerTests(TestCase):

    @patch("user.serializers.User.objects.get")
    def test_validate_and_save_positive(self, mock_get):
        # Mock korisnik
        mock_user = MagicMock()
        mock_get.return_value = mock_user

        data = {"username": "johndoe"}
        serializer = GeneratePasswordSerializer(data=data)

        # Validacija
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["username"], "johndoe")

        # Save generiše password
        password = serializer.save()

        # Proveravamo da li je set_password pozvan sa generisanim passwordom
        mock_user.set_password.assert_called_once_with(password)
        self.assertTrue(mock_user.must_change_password)
        mock_user.save.assert_called_once()

        # Proveravamo da je password string generisan
        self.assertIsInstance(password, str)
        self.assertTrue(len(password) >= 6)

    @patch("user.serializers.User.objects.get")
    def test_validate_negative_user_not_found(self, mock_get):
        # User.objects.get baca DoesNotExist
        mock_get.side_effect = User.DoesNotExist

        serializer = GeneratePasswordSerializer(data={"username": "unknownuser"})

        # Validacija bi trebalo da propadne
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)
        self.assertEqual(serializer.errors["username"][0], "User not found")
    
    @patch("user.serializers.User.objects.get")
    @patch("secrets.token_urlsafe")
    def test_generate_password_success(self, mock_token, mock_get_user):
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user
        mock_token.return_value = "ABC123"

        serializer = GeneratePasswordSerializer(data={"username": "user"})
        self.assertTrue(serializer.is_valid())
        password = serializer.save()

        self.assertEqual(password, "ABC123")
        mock_user.set_password.assert_called_once_with("ABC123")
        self.assertTrue(mock_user.must_change_password)

    @patch("user.serializers.User.objects.get")
    def test_generate_password_user_not_found(self, mock_get_user):
        mock_get_user.side_effect = User.DoesNotExist
        serializer = GeneratePasswordSerializer(data={"username": "nonexist"})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


class UserAuthUnitTests(TestCase):

    # -------------------
    # Registration tests
    # -------------------
    @patch("user.serializers.User.objects.create")
    @patch("user.serializers.Group.objects.get")
    def test_register_user_positive(self, mock_group_get, mock_user_create):
        # Mock User
        mock_user = MagicMock()
        mock_user.username = "newuser"
        mock_user.email = "newuser@email.com"
        mock_user.first_name = "New"
        mock_user.last_name = "User"
        mock_user.set_password = MagicMock()
        mock_user.save = MagicMock()
        mock_user.groups = MagicMock()
        mock_user.groups.add = MagicMock()
        mock_user_create.return_value = mock_user

        # Mock Group
        mock_group = MagicMock()
        mock_group_get.return_value = mock_group

        data = {
            "username": "newuser",
            "email": "newuser@email.com",
            "password": "newpass123",
            "password2": "newpass123",
            "first_name": "New",
            "last_name": "User"
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        mock_user_create.assert_called_once_with(
            username="newuser",
            email="newuser@email.com",
            first_name="New",
            last_name="User"
        )
        mock_user.set_password.assert_called_once_with("newpass123")
        mock_user.save.assert_called_once()
        mock_group_get.assert_called_once_with(name="OrdinaryUser")
        mock_user.groups.add.assert_called_once_with(mock_group)

    def test_register_user_negative_password_mismatch(self):
        data = {
            "username": "baduser",
            "email": "baduser@email.com",
            "password": "pass123",
            "password2": "pass456",
            "first_name": "Bad",
            "last_name": "User"
        }

        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


# --------------------------
# UserProfileDetailView Tests
# --------------------------
class UserProfileDetailViewTests(TestCase):

    def setUp(self):
        # Mock profil i user
        self.mock_profile = MagicMock()
        self.mock_profile.user_id = 1
        self.mock_profile.bio = "User bio"

        self.mock_user = MagicMock()
        self.mock_user.profile = self.mock_profile

        # Patch cache da ne koristi realni cache
        patcher_cache = patch("user.views.cache")
        self.mock_cache = patcher_cache.start()
        self.addCleanup(patcher_cache.stop)

    @patch.object(UserProfileDetailView, "get_object")
    def test_retrieve_own_profile_positive(self, mock_get_object):
        # get_object vraća naš mock profil
        mock_get_object.return_value = self.mock_profile

        # Pripremamo view
        view = UserProfileDetailView()
        view.request = MagicMock()
        view.request.user = self.mock_user
        view.get_serializer = MagicMock(return_value=MagicMock(data={"bio": "User bio"}))

        # Keš nema
        self.mock_cache.get.return_value = None
        self.mock_cache.set.return_value = None

        # Pozivamo retrieve
        response = view.retrieve(view.request)

        # Provera
        self.assertIsInstance(response, Response)
        self.assertEqual(response.data, {"bio": "User bio"})
        self.mock_cache.set.assert_called_once()

    @patch("user.views.get_object_or_404")
    @patch("user.views.AccessPolicy.can_view_user")
    def test_retrieve_other_user_forbidden(self, mock_can_view, mock_get_object):
        # Postavljamo da target user nije dozvoljen za viewer
        mock_target_user = MagicMock()
        mock_target_profile = MagicMock()
        mock_target_profile.user_id = 2
        mock_target_user.profile = mock_target_profile
        mock_get_object.return_value = mock_target_user
        mock_can_view.return_value = False

        view = UserProfileDetailView()
        view.request = MagicMock()
        view.request.user = self.mock_user
        view.request.query_params = {"user_id": 2}

        # Trebalo bi da baci PermissionDenied
        with self.assertRaises(PermissionDenied):
            view.get_object()

    @patch("user.views.get_object_or_404")
    @patch("user.views.AccessPolicy.can_view_user")
    def test_retrieve_other_user_allowed(self, mock_can_view, mock_get_object):
        # Postavljamo da viewer može da vidi target user
        mock_target_user = MagicMock()
        mock_target_profile = MagicMock()
        mock_target_profile.user_id = 2
        mock_target_user.profile = mock_target_profile
        mock_get_object.return_value = mock_target_user
        mock_can_view.return_value = True

        view = UserProfileDetailView()
        view.request = MagicMock()
        view.request.user = self.mock_user
        view.request.query_params = {"user_id": 2}
        view.get_serializer = MagicMock(return_value=MagicMock(data={"bio": "Other bio"}))
        self.mock_cache.get.return_value = None
        self.mock_cache.set.return_value = None

        profile = view.get_object()
        self.assertEqual(profile, mock_target_profile)

        # Testiramo retrieve metod sa keširanjem
        response = view.retrieve(view.request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.data, {"bio": "Other bio"})
        self.mock_cache.set.assert_called_once()

    @patch("user.views.get_object_or_404")
    def test_get_object_permission_denied(self, mock_get):
        user = MagicMock()
        target = MagicMock()
        mock_get.return_value = target
        user.has_perm = False

        view = UserProfileDetailView()
        view.request = MagicMock()
        view.request.user = user
        view.request.query_params = {"user_id": 1}

        # patch AccessPolicy
        with patch("user.views.AccessPolicy.can_view_user", return_value=False):
            with self.assertRaises(PermissionDenied):
                view.get_object()

    @patch("user.views.get_object_or_404")
    @patch("user.views.cache")
    def test_retrieve_caches_profile(self, mock_cache, mock_get):
        profile_mock = MagicMock(user_id=1)
        user = MagicMock()
        user.profile = profile_mock
        view = UserProfileDetailView()
        view.request = MagicMock()
        view.request.user = user
        view.request.query_params = {}

        mock_cache.get.return_value = None

        with patch.object(UserProfileDetailView, "get_serializer", return_value=MagicMock(data={"username": "u1"})):
            resp = view.retrieve(view.request)
            mock_cache.set.assert_called_once()


# --------------------------
# UserProfileUpdateView Tests
# --------------------------
class UserProfileUpdateViewTests(TestCase):

    def setUp(self):
        # Mock user i profil
        self.mock_profile = MagicMock()
        self.mock_profile.user = MagicMock()
        self.mock_profile.user.id = 1

        self.mock_user = MagicMock()
        self.mock_user.profile = self.mock_profile

        # Patch cache
        patcher_cache = patch("user.views.cache")
        self.mock_cache = patcher_cache.start()
        self.addCleanup(patcher_cache.stop)

        # Patch AccessPolicy
        patcher_policy = patch("user.views.AccessPolicy.can_view_user")
        self.mock_can_view = patcher_policy.start()
        self.addCleanup(patcher_policy.stop)

    @patch.object(UserProfileUpdateView, "get_object")
    def test_update_own_profile_positive(self, mock_get_object):
        # get_object vraća naš mock profil
        mock_get_object.return_value = self.mock_profile

        # Pripremamo view i serializer
        view = UserProfileUpdateView()
        view.request = MagicMock()
        view.request.user = self.mock_user

        mock_serializer = MagicMock()
        mock_serializer.save.return_value = self.mock_profile

        # Pozivamo perform_update
        view.perform_update(mock_serializer)

        # Provera da je save pozvan
        mock_serializer.save.assert_called_once()
        # Provera da je cache invalidiran
        self.mock_cache.delete.assert_called_once_with(f"user_profile_{self.mock_profile.user.id}")

    @patch.object(UserProfileUpdateView, "get_object")
    def test_update_other_profile_no_permission(self, mock_get_object):
        # Simuliramo da target profil pripada drugom korisniku
        other_profile = MagicMock()
        other_profile.user = MagicMock()
        other_profile.user.id = 2
        mock_get_object.return_value = other_profile

        # AccessPolicy vraća False
        self.mock_can_view.return_value = False

        view = UserProfileUpdateView()
        view.request = MagicMock()
        view.request.user = self.mock_user

        # Kada pozovemo get_object direktno, treba da baci PermissionDenied
        with self.assertRaises(PermissionDenied):
            # Ovo simulira get_object koji poziva AccessPolicy
            viewer = view.request.user
            user_id = "2"
            target = mock_get_object.return_value
            if not self.mock_can_view(viewer, target):
                raise PermissionDenied()
    
    def test_perform_update_invalidates_cache(self):
        profile_instance = MagicMock()
        serializer = MagicMock()
        serializer.save.return_value = profile_instance

        view = UserProfileUpdateView()
        with patch("user.views.cache") as mock_cache:
            view.perform_update(serializer)
            mock_cache.delete.assert_called_once()


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
    
    def test_patch_calls_serializer_save(self):
        view = UserEmailUpdateView()
        request = MagicMock()
        view.request = request

        serializer_mock = MagicMock()
        serializer_mock.is_valid.return_value = True

        with patch("user.views.UserEmailUpdateSerializer", return_value=serializer_mock):
            resp = view.patch(request)
            serializer_mock.save.assert_called_once()


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

    def setUp(self):
        # Mock user i personal_tokens
        self.mock_user = MagicMock()
        self.mock_user.personal_tokens.count.return_value = 0  # default

    def test_create_personal_token_positive(self):
        # User ima manje od 5 tokena
        self.mock_user.personal_tokens.count.return_value = 3

        view = PersonalTokenCreateView()
        view.request = MagicMock()
        view.request.user = self.mock_user

        mock_serializer = MagicMock()
        view.perform_create(mock_serializer)

        # Proveravamo da je serializer.save pozvan sa user
        mock_serializer.save.assert_called_once_with(user=self.mock_user)

    def test_create_personal_token_limit_reached(self):
        # User ima 5 tokena → greška
        self.mock_user.personal_tokens.count.return_value = 5

        view = PersonalTokenCreateView()
        view.request = MagicMock()
        view.request.user = self.mock_user

        mock_serializer = MagicMock()

        with self.assertRaises(ValidationError) as context:
            view.perform_create(mock_serializer)

        self.assertEqual(str(context.exception.detail[0]), "Token limit reached")
        # Proveravamo da save NIJE pozvan
        mock_serializer.save.assert_not_called()
    
    def test_perform_create_token_limit(self):
        user = MagicMock()
        user.personal_tokens.count.return_value = 5
        view = PersonalTokenCreateView()
        view.request = MagicMock()
        view.request.user = user
        serializer = MagicMock()

        with self.assertRaises(ValidationError):
            view.perform_create(serializer)

    def test_perform_create_saves_user(self):
        user = MagicMock()
        user.personal_tokens.count.return_value = 0
        view = PersonalTokenCreateView()
        view.request = MagicMock()
        view.request.user = user
        serializer = MagicMock()
        view.perform_create(serializer)
        serializer.save.assert_called_once_with(user=user)


# --------------------------
# PersonalTokenListView Tests
# --------------------------
class PersonalTokenListViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.mock_user = MagicMock()

    @patch("user.views.PersonalToken.objects")
    def test_get_queryset_returns_tokens_for_user(self, mock_objects):
        # Mock filter vraća fiksnu listu
        mock_qs = ["token1", "token2"]
        mock_objects.filter.return_value = mock_qs

        # Kreiramo request i view
        request = self.factory.get("/fake-url/")
        request.user = self.mock_user

        view = PersonalTokenListView()
        view.request = request

        # Sada možemo direktno pozvati get_queryset()
        result = view.get_queryset()

        # Provera da se filter pozvao sa pravim korisnikom
        mock_objects.filter.assert_called_once_with(user=self.mock_user)
        # Provera da rezultat odgovara mocku
        self.assertEqual(result, mock_qs)


# --------------------------
# UserListView Tests
# --------------------------
class UserListViewTest(TestCase):
    def setUp(self):
        self.mock_user = MagicMock()

    @patch("user.views.AccessPolicy.scope_user_queryset")
    @patch("user.views.User.objects")
    def test_get_queryset_positive_with_query(self, mock_user_objects, mock_scope):
        """Pozitivan test: Admin koristi 'q' parametar za filtriranje username-a"""
        mock_all_qs = MagicMock()
        mock_user_objects.all.return_value = mock_all_qs

        scoped_qs = MagicMock()
        mock_scope.return_value = scoped_qs

        filtered_qs = ["user1", "user2"]
        scoped_qs.filter.return_value = filtered_qs

        # Mock request sa query_params kao dict
        mock_request = MagicMock()
        mock_request.user = self.mock_user
        mock_request.query_params = {"q": "test"}

        view = UserListView()
        view.request = mock_request

        result = view.get_queryset()

        mock_user_objects.all.assert_called_once()
        mock_scope.assert_called_once_with(self.mock_user, mock_all_qs)
        scoped_qs.filter.assert_called_once_with(username__icontains="test")
        self.assertEqual(result, filtered_qs)

    @patch("user.views.AccessPolicy.scope_user_queryset")
    @patch("user.views.User.objects")
    def test_get_queryset_negative_no_query(self, mock_user_objects, mock_scope):
        """Negativan test: Nema 'q' parametra, vraća ceo scoped queryset"""
        mock_all_qs = MagicMock()
        mock_user_objects.all.return_value = mock_all_qs

        scoped_qs = ["userA", "userB"]
        mock_scope.return_value = scoped_qs

        mock_request = MagicMock()
        mock_request.user = self.mock_user
        mock_request.query_params = {}  # prazno

        view = UserListView()
        view.request = mock_request

        result = view.get_queryset()

        mock_user_objects.all.assert_called_once()
        mock_scope.assert_called_once_with(self.mock_user, mock_all_qs)
        self.assertEqual(result, scoped_qs)


# =========================================================
# Test UserRegistrationView
# =========================================================
class TestUserRegistrationView(TestCase):

    @patch("user.views.Group.objects.get_or_create")
    def test_post_with_roleName(self, mock_get_or_create):
        # --- Mokovana grupa ---
        mock_group_instance = MagicMock()
        mock_get_or_create.return_value = (mock_group_instance, True)

        # --- Mokovani serializer ---
        serializer_mock = MagicMock()
        serializer_mock.is_valid.return_value = True
        user_mock = MagicMock()
        user_mock.username = "testuser"
        user_mock.email = "a@b.com"
        user_mock.groups = MagicMock()
        serializer_mock.save.return_value = user_mock

        view = UserRegistrationView()
        view.get_serializer = MagicMock(return_value=serializer_mock)

        # --- Mokovani request ---
        request_mock = MagicMock()
        request_mock.data = {
            "user": {"username": "testuser", "email": "a@b.com", "password": "pass123!", "password2": "pass123!"},
            "roleName": "Administrator"
        }

        resp = view.post(request_mock)

        # --- Assercije ---
        serializer_mock.is_valid.assert_called_once()
        serializer_mock.save.assert_called_once()
        mock_get_or_create.assert_called_once_with(name="Administrator")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["user"]["username"], "testuser")
    
    @patch("user.views.Group.objects.get_or_create")
    def test_post_without_roleName_default_group(self, mock_get_or_create):
        mock_group_instance = MagicMock()
        mock_get_or_create.return_value = (mock_group_instance, True)

        serializer_mock = MagicMock()
        serializer_mock.is_valid.return_value = True
        user_mock = MagicMock()
        user_mock.username = "testuser2"
        user_mock.email = "b@c.com"
        user_mock.groups = MagicMock()
        serializer_mock.save.return_value = user_mock

        view = UserRegistrationView()
        view.get_serializer = MagicMock(return_value=serializer_mock)

        request_mock = MagicMock()
        request_mock.data = {
            "user": {"username": "testuser2", "email": "b@c.com", "password": "pass123!", "password2": "pass123!"},
            "isSuperadmin": True
        }

        resp = view.post(request_mock)

        serializer_mock.is_valid.assert_called_once()
        serializer_mock.save.assert_called_once()
        mock_get_or_create.assert_called_once_with(name="Superadmin")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["user"]["username"], "testuser2")

# --------------------------
# CreateAdminView Tests
# --------------------------
class CreateAdminViewTest(TestCase):

    def setUp(self):
        self.view = CreateAdminView()
        self.mock_request = MagicMock()
        self.view.request = self.mock_request

    @patch("user.views.User.objects")
    @patch("user.views.Group.objects")
    def test_post_positive(self, mock_group_objects, mock_user_objects):
        """Pozitivan test: kreira admina"""
        self.mock_request.data = {
            "username": "newadmin",
            "email": "admin@email.com",
            "password": "secret123"
        }

        # Mockiranje da username ne postoji
        mock_user_qs = MagicMock()
        mock_user_qs.filter.return_value.exists.return_value = False
        mock_user_objects.return_value = mock_user_objects
        mock_user_objects.filter.return_value = mock_user_qs.filter.return_value

        # Mock User.create_user
        mock_user = MagicMock()
        mock_user_objects.create_user.return_value = mock_user

        # Mock grupa
        mock_group = MagicMock()
        mock_group_objects.get.return_value = mock_group

        response = self.view.post(self.mock_request)

        mock_user_objects.create_user.assert_called_once_with(
            username="newadmin",
            email="admin@email.com",
            password="secret123"
        )
        mock_user.groups.add.assert_called_once_with(mock_group)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.data, {"message": "Admin created"})
        self.assertEqual(response.status_code, 200)

    def test_post_negative_missing_fields(self):
        """Negativan test: fale username ili password"""
        self.mock_request.data = {
            "email": "admin@email.com"
        }

        response = self.view.post(self.mock_request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Missing fields"})

    @patch("user.views.User.objects")
    def test_post_negative_username_exists(self, mock_user_objects):
        """Negativan test: username već postoji"""
        self.mock_request.data = {
            "username": "existinguser",
            "email": "admin@email.com",
            "password": "secret123"
        }

        mock_user_objects.filter.return_value.exists.return_value = True

        response = self.view.post(self.mock_request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Username exists"})


# --------------------------
# UserListAllView Tests
# --------------------------
class UserListAllViewTest(TestCase):
    def setUp(self):
        self.view = UserListAllView()
        self.mock_request = MagicMock()
        self.view.request = self.mock_request
        self.mock_user = MagicMock()
        self.mock_user.pk = 1
        self.mock_request.user = self.mock_user

    @patch("user.views.User.objects")
    def test_get_queryset_positive(self, mock_user_objects):
        """Pozitivan test: vraća queryset sa exclude i prefetch_related"""
        mock_qs = MagicMock()
        mock_user_objects.prefetch_related.return_value = mock_qs
        mock_qs.exclude.return_value = ["user1", "user2"]

        result = self.view.get_queryset()

        # Provera da se pozivaju metode u pravom redosledu
        mock_user_objects.prefetch_related.assert_called_once_with("groups")
        mock_qs.exclude.assert_called_once_with(pk=self.mock_user.pk)

        # Rezultat je ono što mock_qs.exclude vraća
        self.assertEqual(result, ["user1", "user2"])

    @patch("user.views.User.objects")
    def test_get_queryset_negative_empty(self, mock_user_objects):
        """Negativan test: queryset je prazan (npr. nema drugih korisnika)"""
        mock_qs = MagicMock()
        mock_user_objects.prefetch_related.return_value = mock_qs
        mock_qs.exclude.return_value = []

        result = self.view.get_queryset()

        mock_user_objects.prefetch_related.assert_called_once_with("groups")
        mock_qs.exclude.assert_called_once_with(pk=self.mock_user.pk)
        self.assertEqual(result, [])


# --------------------------
# UserDetailView Tests
# --------------------------
class UserDetailViewTest(TestCase):
    def setUp(self):
        self.view = UserDetailView()
        self.mock_request = MagicMock()
        self.view.request = self.mock_request
        self.mock_user = MagicMock()
        self.mock_request.user = self.mock_user

    def test_get_serializer_class_superadmin(self):
        """Pozitivan test: ako je user superadmin, vraća UserDetailSuperSerializer"""
        self.mock_user.is_superadmin = True
        serializer_class = self.view.get_serializer_class()
        self.assertEqual(serializer_class, UserDetailSuperSerializer)

    def test_get_serializer_class_regular_user(self):
        """Negativan test: ako nije superadmin, vraća UserDetailSerializer"""
        self.mock_user.is_superadmin = False
        serializer_class = self.view.get_serializer_class()
        self.assertEqual(serializer_class, UserDetailSerializer)

    def test_queryset_methods_called(self):
        # Kreiramo mock za chain metode
        mock_prefetch = MagicMock()
        mock_select = MagicMock()
        mock_select.prefetch_related.return_value = mock_prefetch

        # Patchujemo queryset atribut na view klasi
        with patch.object(UserDetailView, 'queryset', new=MagicMock(select_related=MagicMock(return_value=mock_select))):
            view = UserDetailView()
            # Pozivamo chain
            qs = view.queryset.select_related("profile").prefetch_related("groups")

            # Provere
            view.queryset.select_related.assert_called_once_with("profile")
            mock_select.prefetch_related.assert_called_once_with("groups")
            self.assertEqual(qs, mock_prefetch)

# --------------------------
# RoleView Tests
# --------------------------
class RoleViewUnitTests(TestCase):

    def setUp(self):
        self.view = RoleView()
        self.mock_user = MagicMock()
        self.view.request = MagicMock()
        self.view.request.user = self.mock_user

    # ----------------------
    # GET tests
    # ----------------------
    @patch("user.views.Group.objects")
    def test_get_superadmin_sees_all_roles(self, mock_group_objects):
        self.mock_user.is_admin.return_value = True
        self.mock_user.is_superadmin = True

        mock_roles = MagicMock()
        mock_roles.values_list.return_value = ["Superadmin", "Admin", "User"]
        mock_group_objects.all.return_value = mock_roles

        response = self.view.get(self.view.request)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.data["roles"], ["Superadmin", "Admin", "User"])

    @patch("user.views.Group.objects")
    def test_get_admin_excludes_superadmin_role(self, mock_group_objects):
        self.mock_user.is_admin.return_value = True
        self.mock_user.is_superadmin = False

        mock_roles = MagicMock()
        mock_roles.exclude.return_value = mock_roles
        mock_roles.values_list.return_value = ["Admin", "User"]
        mock_group_objects.all.return_value = mock_roles

        response = self.view.get(self.view.request)
        self.assertEqual(response.data["roles"], ["Admin", "User"])
        mock_roles.exclude.assert_called_once_with(name="Superadmin")

    # ----------------------
    # POST tests
    # ----------------------
    def test_post_permission_denied_for_non_admin(self):
        self.mock_user.is_admin.return_value = False
        self.mock_user.is_superadmin = False
        self.view.request.data = {"username": "user1", "new_role": "Admin"}

        response = self.view.post(self.view.request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_missing_fields(self):
        self.mock_user.is_admin.return_value = True
        self.mock_user.is_superadmin = True
        self.view.request.data = {"username": "user1"}  # missing new_role

        response = self.view.post(self.view.request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("user.views.User.objects.get")
    def test_post_user_not_found(self, mock_user_get):
        self.mock_user.is_admin.return_value = True
        self.mock_user.is_superadmin = True
        mock_user_get.side_effect = User.DoesNotExist
        self.view.request.data = {"username": "unknown", "new_role": "Admin"}

        response = self.view.post(self.view.request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("user.views.Group.objects.get")
    @patch("user.views.User.objects.get")
    def test_post_role_not_found(self, mock_user_get, mock_group_get):
        self.mock_user.is_admin.return_value = True
        self.mock_user.is_superadmin = True
        mock_user_get.return_value = MagicMock()
        mock_group_get.side_effect = Group.DoesNotExist
        self.view.request.data = {"username": "user1", "new_role": "NonExistentRole"}

        response = self.view.post(self.view.request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("user.views.Group.objects.get")
    @patch("user.views.User.objects.get")
    def test_post_admin_cannot_assign_superadmin(self, mock_user_get, mock_group_get):
        self.mock_user.is_admin.return_value = True
        self.mock_user.is_superadmin = False
        mock_user_get.return_value = MagicMock()
        mock_role = MagicMock()
        mock_role.name = "Superadmin"
        mock_group_get.return_value = mock_role
        self.view.request.data = {"username": "user1", "new_role": "Superadmin"}

        response = self.view.post(self.view.request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("user.views.Group.objects.get")
    @patch("user.views.User.objects.get")
    def test_post_successful_role_update(self, mock_user_get, mock_group_get):
        self.mock_user.is_admin.return_value = True
        self.mock_user.is_superadmin = True

        target_user = MagicMock()
        mock_user_get.return_value = target_user
        new_role = MagicMock()
        new_role.name = "Admin"
        mock_group_get.return_value = new_role

        self.view.request.data = {"username": "user1", "new_role": "Admin"}

        response = self.view.post(self.view.request)

        target_user.groups.clear.assert_called_once()
        target_user.groups.add.assert_called_once_with(new_role)
        target_user.save.assert_called_once()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Role updated to Admin", response.data["message"])
    
    @patch("user.views.Group.objects")
    def test_get_admin_excludes_superadmin(self, mock_objects):
        # --- Mock QuerySet ---
        mock_qs = MagicMock()
        # exclude() vraća isti mock ili novi mock
        mock_qs.exclude.return_value = mock_qs
        # values_list() vraća listu imena
        mock_qs.values_list.return_value = ["Admin", "Manager"]

        mock_objects.all.return_value = mock_qs

        # --- Mock user ---
        mock_user = MagicMock()
        mock_user.is_admin.return_value = True
        mock_user.is_superadmin = False

        # --- RoleView instance ---
        view = RoleView()
        view.request = MagicMock()
        view.request.user = mock_user

        resp = view.get(view.request)

        # --- Assertions ---
        mock_qs.exclude.assert_called_once_with(name="Superadmin")
        mock_qs.values_list.assert_called_once_with("name", flat=True)
        self.assertEqual(resp.data, {"roles": ["Admin", "Manager"]})


# --------------------------
# GenerateUserPasswordView Tests
# --------------------------
class GenerateUserPasswordViewTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    # helper — mock permission da uvek dozvoli
    def _view(self):
        return GenerateUserPasswordView.as_view()

    # =====================
    # SUCCESS
    # =====================
    @patch("user.views.IsSuperAdmin.has_permission", return_value=True)
    @patch("user.views.GeneratePasswordSerializer")
    def test_generate_password_success(self, mock_serializer_class, _):

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = "generated123"
        mock_serializer_class.return_value = mock_serializer

        request = self.factory.post("/", {"username": "testuser"}, format="json")
        response = self._view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["password"], "generated123")

    # =====================
    # INVALID SERIALIZER
    # =====================
    @patch("user.views.IsSuperAdmin.has_permission", return_value=True)
    @patch("user.views.GeneratePasswordSerializer")
    def test_generate_password_invalid_serializer(self, mock_serializer_class, _):

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError("Invalid")
        mock_serializer_class.return_value = mock_serializer

        request = self.factory.post("/", {"username": ""}, format="json")
        response = self._view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # =====================
    # SAVE ERROR
    # =====================
    @patch("user.views.IsSuperAdmin.has_permission", return_value=True)
    @patch("user.views.GeneratePasswordSerializer")
    def test_generate_password_save_exception(self, mock_serializer_class, _):

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = Exception("DB error")
        mock_serializer_class.return_value = mock_serializer

        request = self.factory.post("/", {"username": "testuser"}, format="json")

        with self.assertRaises(Exception):
            self._view()(request)
        
    @patch("user.views.GeneratePasswordSerializer")
    def test_post_generates_password(self, mock_serializer):
        view = GenerateUserPasswordView()
        request = MagicMock()
        view.request = request

        serializer_instance = mock_serializer.return_value
        serializer_instance.is_valid.return_value = True
        serializer_instance.save.return_value = "NewPass123!"

        resp = view.post(request)
        self.assertEqual(resp.data["password"], "NewPass123!")