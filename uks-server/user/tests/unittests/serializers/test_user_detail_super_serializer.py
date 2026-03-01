from django.test import TestCase
from unittest.mock import MagicMock
from django.contrib.auth import get_user_model

from user.serializers import UserDetailSuperSerializer

User = get_user_model()


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

