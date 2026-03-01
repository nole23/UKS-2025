from django.test import TestCase, RequestFactory
from unittest.mock import MagicMock, Mock, patch
from django.contrib.auth import get_user_model

from user.serializers import UserEmailUpdateSerializer
 
User = get_user_model()


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

