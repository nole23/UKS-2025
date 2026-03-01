from django.test import TestCase
from django.contrib.auth import get_user_model
import uuid

from user.models import PersonalToken
from user.models import User

User = get_user_model()


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

