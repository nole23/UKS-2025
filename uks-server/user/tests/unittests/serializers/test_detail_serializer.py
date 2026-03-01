from django.test import TestCase
from types import SimpleNamespace
from user.serializers import UserDetailSerializer
from unittest.mock import MagicMock
from django.contrib.auth import get_user_model

User = get_user_model()


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
