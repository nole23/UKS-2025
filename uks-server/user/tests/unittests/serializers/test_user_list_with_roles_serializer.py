from django.test import TestCase
from unittest.mock import MagicMock, Mock
from django.contrib.auth import get_user_model

from user.serializers import UserListWithRolesSerializer

User = get_user_model()


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