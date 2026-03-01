from django.test import TestCase
from star.serializers import StarUserSerializer
from star.models import Star
from user.models import User
from datetime import datetime


class StarUserSerializerTests(TestCase):

    def setUp(self):
        # Kreiramo fake user i star objekat
        self.user = User(id=1, username="john")
        self.star = Star(user=self.user, repository_id=42, created_at=datetime(2026, 3, 1, 12, 0, 0))

    def test_serializer_single_instance(self):
        """Proverava da li serializer pravilno serializuje jednu Star instancu"""
        serializer = StarUserSerializer(self.star)
        data = serializer.data

        self.assertEqual(data['user_id'], 1)
        self.assertEqual(data['user_username'], "john")
        self.assertEqual(data['starred_at'], "2026-03-01T12:00:00Z")

    def test_serializer_many_instances(self):
        """Proverava da li serializer radi sa više instanci"""
        star2 = Star(user=User(id=2, username="alice"), repository_id=42, created_at=datetime(2026, 3, 1, 13, 0, 0))
        serializer = StarUserSerializer([self.star, star2], many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['user_id'], 1)
        self.assertEqual(data[0]['user_username'], "john")
        self.assertEqual(data[1]['user_id'], 2)
        self.assertEqual(data[1]['user_username'], "alice")

    def test_serializer_read_only_fields(self):
        """Proverava da li su polja read_only"""
        serializer = StarUserSerializer(self.star)
        self.assertTrue(serializer.fields['starred_at'].read_only)
        self.assertTrue(serializer.fields['user_id'].read_only)
        self.assertTrue(serializer.fields['user_username'].read_only)