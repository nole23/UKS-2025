from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from user.models import User, PersonalToken
from django.contrib.auth.models import Group


class UserViewsIntegrationTest(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        Group.objects.create(name="Superadmin")

    # -------------------
    # Registration tests
    # -------------------
    def test_register_user_integration(self):
        """Integracioni test registracije korisnika"""
        data = {
            "username": "intuser",
            "email": "intuser@email.com",
            "password": "Integration123!",
            "password2": "Integration123!",
            "first_name": "Int",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, data, format='json')

        # Proveravamo da li je status 201 CREATED
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Proveravamo da li je korisnik stvarno u bazi
        user = User.objects.get(username="intuser")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "intuser@email.com")
        self.assertTrue(user.check_password("Integration123!"))

        # Proveravamo odgovor JSON-a
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "intuser")
        self.assertEqual(response.data["user"]["email"], "intuser@email.com")
        self.assertIn("message", response.data)

    def test_register_user_integration_password_mismatch(self):
        """Negativan integracioni test: lozinke se ne poklapaju"""
        data = {
            "username": "badintuser",
            "email": "badintuser@email.com",
            "password": "Password1",
            "password2": "Password2",
            "first_name": "Bad",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    # -------------
    # Login tests
    # -------------

    def test_login_user_integration(self):
        """Integracioni test login-a"""
        # Prvo kreiramo korisnika
        user = User.objects.create_user(
            username="loginuser",
            email="loginuser@email.com",
            password="Login123!"
        )

        data = {
            "username": "loginuser",
            "password": "Login123!"
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_user_wrong_password_integration(self):
        """Negativan test login-a sa pogresnom lozinkom"""
        user = User.objects.create_user(
            username="loginuser2",
            email="loginuser2@email.com",
            password="CorrectPass123"
        )

        data = {
            "username": "loginuser2",
            "password": "WrongPass"
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)


class UserProfileIntegrationTests(APITestCase):

    def setUp(self):
        # Registracija korisnika
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "StrongPass123",
            "password2": "StrongPass123",
            "first_name": "Test",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Login
        login_data = {
            "username": "testuser",
            "password": "StrongPass123"
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # URL-ovi
        self.profile_detail_url = reverse('profile-detail')
        self.profile_update_url = reverse('profile-update')
        self.email_update_url = reverse('profile-email-update')
        self.password_change_url = reverse('profile-password-change')
        self.token_create_url = reverse('personal-tokens')

        # Korisnik objekat
        self.user = User.objects.get(username="testuser")

    # ----------------------
    # UserProfileDetailView
    # ----------------------
    def test_get_profile_detail(self):
        response = self.client.get(self.profile_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], "Test")
        self.assertEqual(response.data['last_name'], "User")

    # ----------------------
    # UserProfileUpdateView
    # ----------------------
    def test_update_profile_positive(self):
        data = {
            "first_name": "Updated",
            "last_name": "User",
            "bio": "New bio",
            "avatar": None,
            "company_name": "MyCompany",
            "company_email": "company@example.com",
            "company_website": "https://example.com",
            "company_location": "Serbia",
            "email": "test@example.com"
        }
        response = self.client.put(self.profile_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.profile.bio, "New bio")

    def test_update_profile_negative(self):
        # Email koji već postoji kod drugog usera
        other_user = User.objects.create_user(username="other", email="other@example.com", password="pass123")
        data = {
            "email": "other@example.com"
        }
        response = self.client.put(self.profile_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ----------------------
    # UserEmailUpdateView
    # ----------------------
    def test_patch_email_positive(self):
        data = {"old_email": "test@example.com", "new_email": "newemail@example.com"}
        response = self.client.patch(self.email_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "newemail@example.com")

    def test_patch_email_negative(self):
        data = {"old_email": "wrong@example.com", "new_email": "another@example.com"}
        response = self.client.patch(self.email_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ----------------------
    # UserPasswordChangeView
    # ----------------------
    def test_patch_password_positive(self):
        data = {"old_password": "StrongPass123", "new_password": "NewStrongPass123"}
        response = self.client.patch(self.password_change_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # proveri da li može da se loguje sa novom lozinkom
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass123"))

    def test_patch_password_negative(self):
        data = {"old_password": "WrongPass", "new_password": "NewStrongPass123"}
        response = self.client.patch(self.password_change_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ----------------------
    # PersonalTokenCreateView
    # ----------------------
    def test_create_token_positive(self):
        data = {"name": "MyToken"}
        response = self.client.post(self.token_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token_obj = PersonalToken.objects.get(name="MyToken", user=self.user)
        self.assertIsNotNone(token_obj)

    def test_create_token_negative(self):
        # Pokušaj bez imena
        data = {"name": ""}
        response = self.client.post(self.token_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserExtraIntegrationTests(APITestCase):

    def setUp(self):
        # Kreiranje grupa
        Group.objects.create(name="Superadmin")
        Group.objects.create(name="Administrator")
        Group.objects.create(name="OrdinaryUser")

        # Kreiranje superadmina
        self.superadmin = User.objects.create_user(
            username="superadmin",
            email="superadmin@example.com",
            password="SuperPass123"
        )
        
        # Dodeli Superadmin grupu
        superadmin_group = Group.objects.get(name="Superadmin")
        self.superadmin.groups.add(superadmin_group)
        self.superadmin.save()

        # Login superadmin
        login_url = reverse('token_obtain_pair')
        data = {"username": "superadmin", "password": "SuperPass123"}
        response = self.client.post(login_url, data, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    # ----------------------
    # GenerateUserPasswordView
    # ----------------------
    def test_generate_user_password_superadmin(self):
        url = reverse('reset-password')
        data = {"username": "superadmin"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("password", response.data)

    # ----------------------
    # UserListView
    # ----------------------
    def test_user_list_view(self):
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    # ----------------------
    # CreateAdminView
    # ----------------------
    def test_create_admin(self):
        url = reverse('create-admin-view')
        data = {"username": "newadmin", "email": "newadmin@example.com", "password": "Admin123!"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newadmin").exists())

    # ----------------------
    # UserListAllView
    # ----------------------
    def test_user_list_all_view(self):
        url = reverse('user-list-all')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    # ----------------------
    # UserDetailView
    # ----------------------
    def test_user_detail_view(self):
        # Kreiranje običnog korisnika
        user = User.objects.create_user(username="detailuser", email="detail@example.com", password="Pass123")
        url = reverse('user-detail-view', kwargs={"username": "detailuser"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], "detailuser")

    # ----------------------
    # RoleView GET
    # ----------------------
    def test_role_list_get(self):
        url = reverse('role-list-all')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("roles", response.data)
        self.assertIsInstance(response.data["roles"], list)

    # ----------------------
    # RoleView POST
    # ----------------------
    def test_role_update_post(self):
        # Kreiranje običnog korisnika
        user = User.objects.create_user(username="roleuser", email="role@example.com", password="Pass123")
        url = reverse('role-list-all')
        data = {"username": "roleuser", "new_role": "Administrator"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.groups.filter(name="Administrator").exists())

    # ----------------------
    # PersonalTokenListView
    # ----------------------
    def test_personal_token_list_view(self):
        # Kreiranje tokena
        PersonalToken.objects.create(name="Token1", user=self.superadmin)
        url = reverse('personal-tokens-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        self.assertEqual(response.data[0]['name'], "Token1")