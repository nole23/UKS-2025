from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from user.models import User
from Organization.models import Organization
from repository.models import Repository

# Dohvata trenutno aktivan User model (može biti custom)
User = get_user_model()


# Test klasa za model Repository
class RepositoryModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="user@test.com", password="pass")
        self.org = Organization.objects.create(name="TestOrg", owner=self.user)

    # Testira kreiranje repozitorijuma sa vlasnikom
    def test_create_repository_with_owner(self):
        repo = Repository.objects.create(
            name="MyRepo",
            description="Test repository",
            visibility="public",
            owner=self.user,
            badge="OFFICIAL"
        )
        self.assertEqual(repo.name, "MyRepo")
        self.assertEqual(repo.owner, self.user)
        self.assertEqual(repo.visibility, "public")
        self.assertEqual(repo.badge, "OFFICIAL")
        self.assertIsNone(repo.organization)
        self.assertEqual(str(repo), "MyRepo")

    # Testira kreiranje repozitorijuma sa organizacijom umesto vlasnika
    def test_create_repository_with_organization(self):
        repo = Repository.objects.create(
            name="OrgRepo",
            description="Org repository",
            visibility="private",
            organization=self.org
        )
        self.assertEqual(repo.organization, self.org)
        self.assertIsNone(repo.owner)
        self.assertEqual(repo.visibility, "private")

    # Testira default vrednosti za broj zvezdica i pull requestova
    def test_stars_and_pulls_default(self):
        repo = Repository.objects.create(
            name="StatsRepo",
            visibility="public"
        )
        self.assertEqual(repo.stars_count, 0)
        self.assertEqual(repo.pulls_count, 0)

    # Testira da li last_pushed_at može biti null i da li se može postaviti
    def test_last_pushed_at_nullable(self):
        repo = Repository.objects.create(
            name="PushRepo",
            visibility="public"
        )
        self.assertIsNone(repo.last_pushed_at)
        now = timezone.now()
        repo.last_pushed_at = now
        repo.save()
        self.assertEqual(repo.last_pushed_at, now)
    
    # Testira validaciju polja visibility
    def test_invalid_visibility(self):
        repo = Repository(name="BadRepo", visibility="wrong")
        with self.assertRaises(Exception):
            repo.full_clean()
    
    # Testira da li brisanje korisnika briše i njegove repozitorijume (CASCADE)
    def test_delete_owner_deletes_repo(self):
        repo = Repository.objects.create(name="R", visibility="public", owner=self.user)
        self.user.delete()
        self.assertFalse(Repository.objects.filter(id=repo.id).exists())

    # Testira da li brisanje organizacije briše repozitorijume koji pripadaju organizaciji
    def test_delete_org_deletes_repo(self):
        repo = Repository.objects.create(name="R", visibility="public", organization=self.org)
        self.org.delete()
        self.assertFalse(Repository.objects.filter(id=repo.id).exists())

    # Testira da li se created_at automatski postavlja pri kreiranju
    def test_created_at_auto_set(self):
        repo = Repository.objects.create(name="TimeRepo", visibility="public")
        self.assertIsNotNone(repo.created_at)

    # Testira default vrednost za badge
    def test_badge_default(self):
        repo = Repository.objects.create(name="BadgeRepo", visibility="public")
        self.assertEqual(repo.badge, "NONE")
    
    # Testira da li su indeksi za polja name i visibility postavljeni
    def test_indexes_exist(self):
        indexes = [f.name for f in Repository._meta.fields if f.db_index]
        self.assertIn("name", indexes)
        self.assertIn("visibility", indexes)