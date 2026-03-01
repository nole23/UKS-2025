from django.test import TestCase
from unittest.mock import MagicMock
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

from user.serializers import PersonalTokenSerializer
from user.models import PersonalToken

User = get_user_model()


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
