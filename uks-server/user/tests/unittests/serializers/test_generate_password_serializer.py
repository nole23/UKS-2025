from django.test import TestCase
from rest_framework.exceptions import ValidationError
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from user.models import User
from user.serializers import GeneratePasswordSerializer

User = get_user_model()


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
