from django.test import TestCase, RequestFactory
from rest_framework.exceptions import ValidationError
from unittest.mock import MagicMock, Mock
from django.contrib.auth import get_user_model

from user.serializers import UserPasswordChangeSerializer

User = get_user_model()


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