
from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from user.models import User
from repository.models import Repository, RepositoryCollaborator

User = get_user_model()


# Test klasa za model RepositoryCollaborator
class RepositoryRepositoryCollaboratorTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", email="user1@test.com", password="pass")
        self.user2 = User.objects.create_user(username="user2", email="user2@test.com", password="pass")
        self.repo = Repository.objects.create(name="CollabRepo", visibility="public", owner=self.user1)

    # Testira dodavanje saradnika u repozitorijum
    def test_add_collaborator(self):
        collab = RepositoryCollaborator.objects.create(
            repository=self.repo,
            user=self.user2,
            role="write"
        )
        self.assertEqual(collab.repository, self.repo)
        self.assertEqual(collab.user, self.user2)
        self.assertEqual(collab.role, "write")
        self.assertEqual(str(collab), f"{self.user2} - write on {self.repo}")

    # Testira jedinstvenost saradnika po repozitorijumu (unique_together)
    def test_unique_collaborator_per_user_repository(self):
        RepositoryCollaborator.objects.create(
            repository=self.repo,
            user=self.user2,
            role="read"
        )
        with self.assertRaises(IntegrityError):
            RepositoryCollaborator.objects.create(
                repository=self.repo,
                user=self.user2,
                role="admin"
            )

    # Testira reverse relacije (da li možemo dohvatiti sve saradnike repozitorijuma i uloge korisnika)
    def test_repository_collaborators_reverse_relation(self):
        collab = RepositoryCollaborator.objects.create(
            repository=self.repo,
            user=self.user2,
            role="admin"
        )
        self.assertIn(collab, self.repo.collaborators.all())
        self.assertIn(collab, self.user2.repository_roles.all())
    
    # Testira da li brisanje repozitorijuma briše i sve saradnike
    def test_delete_repo_deletes_collaborators(self):
        collab = RepositoryCollaborator.objects.create(
            repository=self.repo,
            user=self.user2,
            role="read"
        )
        self.repo.delete()
        self.assertFalse(RepositoryCollaborator.objects.filter(id=collab.id).exists())
    
    # Testira validaciju za nevalidnu ulogu
    def test_invalid_role(self):
        collab = RepositoryCollaborator(
            repository=self.repo,
            user=self.user2,
            role="invalid"
        )
        with self.assertRaises(Exception):
            collab.full_clean()
