from django.test import TestCase
from django.db import IntegrityError
from django.utils import timezone
from user.models import User
from repository.models import Repository
from star.models import Star

class StarModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="john", email="john@example.com")
        self.repo = Repository.objects.create(
            name="TestRepo",
            visibility="public",
            owner=self.user
        )

    def test_create_star(self):
        """Proverava da li se star može kreirati"""
        star = Star.objects.create(user=self.user, repository=self.repo)
        self.assertEqual(star.user, self.user)
        self.assertEqual(star.repository, self.repo)
        self.assertIsNotNone(star.created_at)
        self.assertTrue(isinstance(star.created_at, timezone.datetime))

    def test_unique_together_constraint(self):
        """Proverava da se ne može kreirati dva puta isti star za istog usera i repo"""
        Star.objects.create(user=self.user, repository=self.repo)
        with self.assertRaises(IntegrityError):
            Star.objects.create(user=self.user, repository=self.repo)

    def test_multiple_users_same_repository(self):
        """Različiti korisnici mogu da stavljaju star na isti repo"""
        user2 = User.objects.create(username="alice", email="alice@example.com")
        Star.objects.create(user=self.user, repository=self.repo)
        star2 = Star.objects.create(user=user2, repository=self.repo)
        self.assertEqual(Star.objects.count(), 2)
        self.assertIn(star2, Star.objects.all())

    def test_same_user_multiple_repositories(self):
        """Isti korisnik može da stavi star na više repozitorijuma"""
        repo2 = Repository.objects.create(name="Repo2", visibility="public", owner=self.user)
        star1 = Star.objects.create(user=self.user, repository=self.repo)
        star2 = Star.objects.create(user=self.user, repository=repo2)
        self.assertEqual(Star.objects.count(), 2)
        self.assertIn(star1, Star.objects.all())
        self.assertIn(star2, Star.objects.all())