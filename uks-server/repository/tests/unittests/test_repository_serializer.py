from django.test import TestCase
from unittest.mock import MagicMock
from repository.serializer import RepositorySerializer

class RepositorySerializerUnitTests(TestCase):
    def setUp(self):
        # Kreiramo "mock" owner i organization
        self.mock_owner = MagicMock()
        self.mock_owner.username = "mockuser"

        self.mock_org = MagicMock()
        self.mock_org.name = "mockorg"

        # Kreiramo mock repository instancu
        self.mock_repo = MagicMock()
        self.mock_repo.id = 1
        self.mock_repo.name = "TestRepo"
        self.mock_repo.description = "A test repository"
        self.mock_repo.visibility = "public"
        self.mock_repo.created_at = "2026-02-07T12:00:00Z"
        self.mock_repo.owner = self.mock_owner
        self.mock_repo.organization = self.mock_org
        self.mock_repo.last_pushed_at = "2026-02-07T13:00:00Z"
        self.mock_repo.stars_count = 5
        self.mock_repo.pulls_count = 2
        self.mock_repo.badge = "OFFICIAL"

    # Pozitivan test: proverava da serializer vraća očekivane vrednosti.
    def test_repository_serializer_positive(self):
        """
        Pozitivan test: proverava da serializer vraća očekivane vrednosti.
        """
        serializer = RepositorySerializer(instance=self.mock_repo)
        data = serializer.data

        # Proveravamo da polja odgovaraju vrednostima iz mock objekta
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["name"], "TestRepo")
        self.assertEqual(data["description"], "A test repository")
        self.assertEqual(data["visibility"], "public")
        self.assertEqual(data["created_at"], "2026-02-07T12:00:00Z")
        self.assertEqual(data["owner_username"], "mockuser")
        self.assertEqual(data["organization_name"], "mockorg")
        self.assertEqual(data["last_pushed_at"], "2026-02-07T13:00:00Z")
        self.assertEqual(data["stars_count"], 5)
        self.assertEqual(data["pulls_count"], 2)
        self.assertEqual(data["badge"], "OFFICIAL")

    # Ovaj test simulira pogrešno korišćenje serializer-a.
    def test_repository_serializer_negative_invalid_field(self):
        """
        Negativan test: proverava da serializer baca grešku kada polje ne postoji.
        Ovaj test simulira pogrešno korišćenje serializer-a.
        """
        serializer = RepositorySerializer(instance=self.mock_repo)
        data = serializer.data

        # Pokušavamo da pristupimo nepostojećem polju
        with self.assertRaises(KeyError):
            _ = data["non_existent_field"]