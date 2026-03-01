from django.test import TestCase
from unittest.mock import MagicMock, Mock, patch
from django.contrib.auth import get_user_model

from user.serializers import UserProfileDetailSerializer

User = get_user_model()


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