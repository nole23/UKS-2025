from django.test import TestCase
from rest_framework import status
from unittest.mock import MagicMock, patch
from rest_framework.response import Response
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from user.models import User
from user.views import RoleView

User = get_user_model()

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
