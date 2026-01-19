from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from user.models import User
from repository.models import Repository
from Organization.models import Organization

class RepositoryListViewIntegrationTests(APITestCase):

    def setUp(self):
        # ----------------------
        # URL-ovi
        # ----------------------
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.repo_url = reverse('repository-list')
        self.search_url = reverse('repository-search')

        # ----------------------
        # Kreiranje i registracija korisnika
        # ----------------------
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "strongpass123",
            "password2": "strongpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # ----------------------
        # Login i čuvanje JWT tokena
        # ----------------------
        login_data = {
            "username": "testuser",
            "password": "strongpass123"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    # ----------------------
    # GET metoda - integracioni test za RepositoryListView
    # ----------------------
    def test_get_public_repositories(self):
        # Kreiranje repozitorijuma direktno u bazi
        user = User.objects.get(username="testuser")
        Repository.objects.create(name="PublicRepo1", visibility="public", owner=user)
        Repository.objects.create(name="PrivateRepo1", visibility="private", owner=user)

        response = self.client.get(self.repo_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "PublicRepo1")

    # ----------------------
    # POST metoda - integracioni test za RepositoryListView
    # ----------------------
    def test_post_create_repository(self):
        data = {
            "name": "NewPublicRepo",
            "description": "Test repo",
            "visibility": "public"
        }

        response = self.client.post(self.repo_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "NewPublicRepo")

        # Provera da li je repo sačuvan u bazi
        repo = Repository.objects.get(name="NewPublicRepo")
        self.assertEqual(repo.owner.username, "testuser")
        self.assertEqual(repo.visibility, "public")

    # ----------------------
    # GET metoda - integracioni test za RepositorySearchView
    # ----------------------
    def test_search_repository(self):
        user = User.objects.get(username="testuser")
        Repository.objects.create(name="SearchMe", visibility="public", owner=user)
        Repository.objects.create(name="DoNotFindMe", visibility="private", owner=user)

        # Search po imenu
        response = self.client.get(self.search_url, {'q': 'SearchMe'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "SearchMe")

    # ----------------------
    # GET metoda - search bez rezultata (negativan test)
    # ----------------------
    def test_search_repository_not_found(self):
        # Nema nijednog repo sa ovim query-em
        response = self.client.get(self.search_url, {'q': 'NonExistent'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class RepositorySearchViewIntegrationTests(APITestCase):

    def setUp(self):
        # kreiraj usera
        self.user_data = {
            "username": "searchuser",
            "email": "search@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "first_name": "Search",
            "last_name": "User"
        }
        self.register_url = reverse('register')
        self.client.post(self.register_url, self.user_data, format='json')

        # login
        login_url = reverse('token_obtain_pair')
        login_resp = self.client.post(login_url, {"username": "searchuser", "password": "testpass123"}, format='json')
        self.token = login_resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        # user object
        self.user = User.objects.get(username="searchuser")

        # organizacija
        self.organization = Organization.objects.create(name="TestOrg", owner=self.user)

        # repo-i
        self.repo1 = Repository.objects.create(
            name="RepoOne",
            owner=self.user,
            organization=self.organization,
            visibility="public"  # <--- mora biti public
        )

        self.repo2 = Repository.objects.create(
            name="RepoTwo",
            owner=self.user,
            organization=self.organization,
            visibility="public"  # <--- mora biti public
        )
        self.repo3 = Repository.objects.create(name="HiddenRepo", visibility="private", owner=self.user)

        # URL za search
        self.search_url = reverse('repository-search')

    # ----------------------
    # Pozitivan test - search po imenu
    # ----------------------
    def test_search_by_name(self):
        response = self.client.get(self.search_url, {'q': 'RepoOne'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "RepoOne")

    # ----------------------
    # Pozitivan test - search po organizaciji
    # ----------------------
    def test_search_by_organization(self):
        response = self.client.get(self.search_url, {'q': 'TestOrg'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['organization_name'], self.organization.name)

    # ----------------------
    # Pozitivan test - search po owneru
    # ----------------------
    def test_search_by_owner(self):
        response = self.client.get(self.search_url, {'q': 'searchuser'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Trebalo bi da vrati samo public repozitorijume
        self.assertEqual(len(response.data), 2)
        repo_names = [r['name'] for r in response.data]
        self.assertIn("RepoOne", repo_names)
        self.assertIn("RepoTwo", repo_names)

    # ----------------------
    # Negativan test - search bez rezultata
    # ----------------------
    def test_search_no_results(self):
        response = self.client.get(self.search_url, {'q': 'NonExistentRepo'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
