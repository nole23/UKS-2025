from logging import Logger

from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group

from rest_framework import generics, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError

from rest_framework_simplejwt.views import TokenObtainPairView

from .permissions import IsAdminOrSelf, IsAdminOrSuperAdmin, IsSuperAdmin, IsUser, MustChangePasswordBlocker
from .serializers import (
    GeneratePasswordSerializer,
    MyTokenObtainPairSerializer,
    UserDetailSerializer,
    UserDetailSuperSerializer,
    UserListWithRolesSerializer,
    UserRegistrationSerializer,
    UserProfileDetailSerializer,
    UserProfileUpdateSerializer,
    UserEmailUpdateSerializer,
    UserPasswordChangeSerializer,
    PersonalTokenSerializer,
    UserListSerializer
)
from .models import PersonalToken, User
from .access_policies import AccessPolicy
from utils.logger import UKSAuditLogger, UKSLogger


# =========================================================
# REGISTER USER (ADMIN + SUPERADMIN)
# =========================================================
"""
request:
{
    "username": "",
    "email": "",
    "password": "",
    "password2": "",
    "first_name": "",
    "last_name": ""
}
reposne:
{
    "user": {
        "username": "",
        "email": ""
    },
    "message": "User registered successfully"
}
"""
class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]  # <-- ovo omogućava pristup svima

    def post(self, request, *args, **kwargs):
        UKSLogger.debug("Registration request received")
        user_data = self._get_user_data(request)
        group = self._get_user_group(request)
        serializer = self._validate_serializer(user_data)
        user = self._create_user(serializer, group)
        UKSLogger.debug("Registration completed successfully")

        return self._build_response(user)
    
    def _get_user_data(self, request):
        user_data = request.data.get("user", request.data)
        if not user_data:
            UKSLogger.warning("Registration request without user data")
        return user_data

    def _get_user_group(self, request):
        role_name = request.data.get("roleName")
        if role_name:
            UKSLogger.debug(f"Requested role: {role_name}")
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                UKSLogger.info(f"New role auto-created: {role_name}")
        else:
            is_super = request.data.get("isSuperadmin", False)
            default_group_name = "Superadmin" if is_super else "OrdinaryUser"
            UKSLogger.debug(f"No role provided, using default: {default_group_name}")
            group, _ = Group.objects.get_or_create(name=default_group_name)
        return group

    def _validate_serializer(self, user_data):
        serializer = self.get_serializer(data=user_data)
        try:
            serializer.is_valid(raise_exception=True)
            UKSLogger.debug("Registration serializer validation passed")
        except Exception as ex:
            UKSLogger.error(f"Registration validation failed: {ex}")
            raise
        return serializer

    def _create_user(self, serializer, group):
        try:
            user = serializer.save()
            user.groups.add(group)
            UKSLogger.info(
                f"User created successfully username={user.username} group={group.name}"
            )
        except Exception as ex:
            UKSLogger.critical(f"User creation failed: {ex}")
            raise
        return user

    def _build_response(self, user):
        return Response(
            {
                "user": {"username": user.username, "email": user.email},
                "message": "User registered successfully",
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# LOGIN
# =========================================================
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]
    

# =========================================================
# PROFILE DETAIL
# =========================================================
class UserProfileDetailView(generics.RetrieveAPIView):
    """
    User → vidi svoj profil
    Superadmin → može dohvatiti bilo čiji profil
    """
    serializer_class = UserProfileDetailSerializer
    permission_classes = [IsUser, MustChangePasswordBlocker]

    """
    Vrati stvarnu instancu modela UserProfile.
    Ovo je obavezno da bi integracioni testovi i DRF serializer radili.
    """
    def get_object(self):
        UKSLogger.debug("Get user profile started...")

        viewer = self.request.user
        user_id = self.request.query_params.get("user_id")
        UKSLogger.debug(f"Request received for user_id={user_id}")

        if user_id:
            try:
                target = get_object_or_404(User, pk=user_id)
                UKSLogger.info(f"Target user fetched: {target.username}")
            except Exception as ex:
                UKSLogger.error(f"Could not fetch user with id={user_id}: {ex}")
                raise

            if not AccessPolicy.can_view_user(viewer, target):
                UKSLogger.warning(f"Access denied to user_id={user_id}")
                UKSAuditLogger.info(f"{viewer.username} | PERMISSION_DENIED for user_id={user_id}")
                raise PermissionDenied()
            
            UKSAuditLogger.info(f"{viewer.username} | ACCESS_GRANTED for user_id={user_id}")
            UKSLogger.debug("Get user profile ended...")
            return target.profile
        
        UKSAuditLogger.info(f"{viewer.username} | ACCESS_SELF_PROFILE")
        UKSLogger.debug("Get user profile ended...")
        return viewer.profile

    """
    Override retrieve da podrži keširanje serijalizovanih podataka.
    """
    def retrieve(self, request, *args, **kwargs): 
        UKSLogger.debug("Retrieve profile started...")

        profile = self.get_object()
        cache_key = f"user_profile_{profile.user_id}"

        profile_data = cache.get(cache_key)
        if profile_data:
            UKSLogger.info(f"Cache hit for key={cache_key}")
        else:
            UKSLogger.info(f"Cache miss for key={cache_key}, serializing")
            # Serijalizuj
            serializer = self.get_serializer(profile)
            profile_data = serializer.data
            # Sačuvaj u keš 5 minuta
            cache.set(cache_key, profile_data, 300)
            UKSLogger.info(f"Profile cached for key={cache_key}")

        UKSLogger.debug("Retrieve profile ended...")
        return Response(profile_data)


# =========================================================
# PROFILE UPDATE
# =========================================================
"""
PUT request: 
{
    "first_name": "",
    "last_name": "",
    "bio": "",
    "avatar": null,
    "company_name": "",
    "company_email": "",
    "company_website": "",
    "company_location": "",
    "email": ""
}
"""
class UserProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [IsUser]

    def get_object(self):
        UKSLogger.debug("Get object starded...")

        viewer = self.request.user
        user_id = self.request.query_params.get("user_id")
        UKSLogger.debug(f"Request received for user_id={user_id}")

        if user_id:
            try:
                target = get_object_or_404(User, pk=user_id)
                UKSLogger.info(f"Target user fetched: {target.username}")
            except Exception as ex:
                UKSLogger.error(f"Could not fetch user with id={user_id}: {ex}")
                raise

            if not AccessPolicy.can_view_user(viewer, target):
                UKSLogger.warning(f"Access denied to user_id={user_id}")
                UKSAuditLogger.info(f"{viewer.username} | PERMISSION_DENIED for user_id={user_id}")
                raise PermissionDenied()

            UKSAuditLogger.info(f"{viewer.username} | ACCESS_GRANTED for user_id={user_id}")
            UKSLogger.debug("Get object ended...")
            return target.profile
        
        UKSAuditLogger.info(f"{viewer.username} | ACCESS_SELF_PROFILE")
        UKSLogger.debug("Get object ended...")
        return viewer.profile
    
    def perform_update(self, serializer):
        UKSLogger.debug("Update profile starded...")
        try:
            instance = serializer.save()
            UKSLogger.info(f"User profile updated successfully for user_id={instance.user.id}")

            # invalidate cache
            cache_key = f"user_profile_{instance.user.id}"
            cache.delete(cache_key)
            UKSLogger.info(f"Cache invalidated for key={cache_key}")

            UKSAuditLogger.info(f"{self.request.user.username} | PROFILE_UPDATED user_id={instance.user.id}")
        except Exception as ex:
            UKSLogger.error(f"Profile update failed: {ex}")
            raise
        finally:
            UKSLogger.debug("Update profile ended...")


# =========================================================
# EMAIL CHANGE
# =========================================================
"""
PATCH request: 
{
    "old_email": "",
    "new_email": ""
}
"""
class UserEmailUpdateView(APIView):
    permission_classes = [IsUser]

    def patch(self, request):
        UKSLogger.debug("Update email started...")
        try:
            serializer = UserEmailUpdateSerializer(
                data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)

            user = serializer.save()
            # Audit log
            UKSAuditLogger.info(f"{request.user.username} | UPDATE_EMAIL | success")

            UKSLogger.info(f"User {request.user.username} updated email to {user.email}")

            return Response(
                {"message": "Email updated successfully"},
                status=status.HTTP_200_OK
            )

        except ValidationError as ve:
            UKSLogger.warning(f"Validation failed: {ve}")
            UKSAuditLogger.info(f"{request.user.username} | UPDATE_EMAIL | validation_failed")
            raise

        except Exception as ex:
            UKSLogger.error(f"Email update failed: {ex}")
            UKSAuditLogger.info(f"{request.user.username} | UPDATE_EMAIL | failed")
            raise

        finally:
            UKSLogger.debug("Update email ended...")


# =========================================================
# PASSWORD CHANGE
# =========================================================
"""
PATCH request: 
{
    "old_password": "",
    "new_password": ""
}
"""
class UserPasswordChangeView(APIView):
    permission_classes = [IsAdminOrSelf]

    def patch(self, request):
        UKSLogger.debug("Password change started...")
        try:
            serializer = UserPasswordChangeSerializer(
                data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)

            serializer.save()

            # Audit log
            UKSAuditLogger.info(f"{request.user.username} | CHANGE_PASSWORD | success")
            UKSLogger.info(f"User {request.user.username} changed password successfully")

            return Response(
                {"message": "Password changed successfully"},
                status=status.HTTP_200_OK
            )

        except ValidationError as ve:
            UKSLogger.warning(f"Password change validation failed: {ve}")
            UKSAuditLogger.info(f"{request.user.username} | CHANGE_PASSWORD | validation_failed")
            raise

        except Exception as ex:
            UKSLogger.error(f"Password change failed: {ex}")
            UKSAuditLogger.info(f"{request.user.username} | CHANGE_PASSWORD | failed")
            raise

        finally:
            UKSLogger.debug("Password change ended...")


# =========================================================
# PERSONAL TOKEN CREATE
# =========================================================
"""
POST request: 
{
    "name": ""
}
"""
class PersonalTokenCreateView(generics.CreateAPIView):
    serializer_class = PersonalTokenSerializer
    permission_classes = [IsUser]

    def perform_create(self, serializer):
        UKSLogger.debug("Personal token creation started...")
        try:
            user = self.request.user

            if user.personal_tokens.count() >= 5:
                UKSLogger.warning(f"User {user.username} attempted to create token but limit reached")
                UKSAuditLogger.info(f"{user.username} | CREATE_PERSONAL_TOKEN | limit_reached")
                raise ValidationError("Token limit reached")

            serializer.save(user=user)

            UKSLogger.info(f"User {user.username} created a new personal token")
            UKSAuditLogger.info(f"{user.username} | CREATE_PERSONAL_TOKEN | success")

        except ValidationError as ve:
            # već logovano u warning
            raise ve

        except Exception as ex:
            UKSLogger.error(f"Personal token creation failed for user {user.username}: {ex}")
            UKSAuditLogger.info(f"{user.username} | CREATE_PERSONAL_TOKEN | failed")
            raise

        finally:
            UKSLogger.debug("Personal token creation ended...")


# =========================================================
# PERSONAL TOKEN LIST
# =========================================================
class PersonalTokenListView(generics.ListAPIView):
    serializer_class = PersonalTokenSerializer
    permission_classes = [IsAdminOrSelf]

    def get_queryset(self):
        UKSLogger.debug("Personal token list retrieval started...")
        user = self.request.user

        try:
            queryset = PersonalToken.objects.filter(user=user)
            count = queryset.count()

            UKSLogger.info(f"User {user.username} retrieved {count} personal tokens")
            UKSAuditLogger.info(f"{user.username} | LIST_PERSONAL_TOKENS | count={count}")

            return queryset

        except Exception as ex:
            UKSLogger.error(f"Failed to retrieve personal tokens for user {user.username}: {ex}")
            UKSAuditLogger.info(f"{user.username} | LIST_PERSONAL_TOKENS | failed")
            raise

        finally:
            UKSLogger.debug("Personal token list retrieval ended...")
    

# =========================================================
# USER LIST
# =========================================================
class UserListView(ListAPIView):
    """
    Admin vidi sve osim superadmina
    Superadmin vidi sve
    """
    serializer_class = UserListSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_queryset(self):
        UKSLogger.debug("User list retrieval started...")
        viewer = self.request.user

        try:
            qs = AccessPolicy.scope_user_queryset(viewer, User.objects.all())
            q = self.request.query_params.get("q")

            if q:
                qs = qs.filter(username__icontains=q)
                UKSLogger.info(f"Filtering users with query: '{q}'")

            count = qs.count()
            UKSLogger.info(f"User {viewer.username} retrieved {count} users")
            UKSAuditLogger.info(f"{viewer.username} | LIST_USERS | count={count}")

            return qs

        except Exception as ex:
            UKSLogger.error(f"Failed to retrieve user list for {viewer.username}: {ex}")
            UKSAuditLogger.info(f"{viewer.username} | LIST_USERS | failed")
            raise

        finally:
            UKSLogger.debug("User list retrieval ended...")


# =========================================================
# CREATE ADMIN (SUPERADMIN ONLY)
# =========================================================
"""
POST /admin/create-admin
{
  "username": "admin1",
  "email": "admin@example.com",
  "password": "Pass123!"
}

Response 201:
{
  "message": "Admin created"
}
"""
class CreateAdminView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        UKSLogger.debug("Create admin started...")
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        viewer = request.user

        try:
            if not username or not password:
                UKSLogger.warning(f"Admin creation failed: missing fields by {viewer.username}")
                return Response({"error": "Missing fields"}, status=400)

            if User.objects.filter(username=username).exists():
                UKSLogger.warning(f"Admin creation failed: username '{username}' exists by {viewer.username}")
                return Response({"error":"Username exists"}, status=400)

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            admin_group = Group.objects.get(name="Administrator")
            user.groups.add(admin_group)

            UKSLogger.info(f"Admin '{username}' created successfully by {viewer.username}")
            UKSAuditLogger.info(f"{viewer.username} | CREATE_ADMIN | created {username}")

            return Response({"message": "Admin created"}, status=status.HTTP_201_CREATED)

        except Exception as ex:
            UKSLogger.error(f"Admin creation failed by {viewer.username}: {ex}")
            UKSAuditLogger.info(f"{viewer.username} | CREATE_ADMIN | failed")
            raise

        finally:
            UKSLogger.debug("Create admin ended...")
    

# =========================================================
# GET ALL USERS (SUPERADMIN ADMIN ADN SUPERADMIN)
# =========================================================
class UserListAllView(ListAPIView):
    """
    Admin vidi sve korisnike, uključujući superadmina, ali ne može ih menjati.
    Superadmin vidi sve i može editovati.
    """
    serializer_class = UserListWithRolesSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_queryset(self):
        UKSLogger.debug("User list retrieval started...")
        viewer = self.request.user

        try:
            # vraća sve korisnike bez ikakvih filtera, osim trenutnog usera
            qs = User.objects.prefetch_related("groups").exclude(pk=viewer.pk)
            UKSLogger.info(f"User list retrieved successfully by {viewer.username} (count={qs.count()})")
            UKSAuditLogger.info(f"{viewer.username} | GET_ALL_USERS | retrieved {qs.count()} users")
            return qs

        except Exception as ex:
            UKSLogger.error(f"Failed to retrieve user list by {viewer.username}: {ex}")
            UKSAuditLogger.info(f"{viewer.username} | GET_ALL_USERS | failed")
            raise

        finally:
            UKSLogger.debug("User list retrieval ended...")


# =========================================================
# GET ONE USER
# =========================================================
class UserDetailView(RetrieveAPIView):
    permission_classes = [IsAdminOrSelf]
    lookup_field = "username"
    queryset = User.objects.select_related("profile").prefetch_related("groups")

    def get_serializer_class(self):
        return UserDetailSuperSerializer if self.request.user.is_superadmin else UserDetailSerializer

    def get_object(self):
        UKSLogger.debug("User detail retrieval started...")
        viewer = self.request.user
        username = self.kwargs.get(self.lookup_field)

        try:
            user = super().get_object()

            # proveravamo dozvolu pristupa
            if not AccessPolicy.can_view_user(viewer, user):
                UKSLogger.warning(f"Access denied for {viewer.username} to view {username}")
                UKSAuditLogger.info(f"{viewer.username} | GET_USER_DETAIL | access_denied {username}")
                raise PermissionDenied()

            UKSLogger.info(f"User {username} retrieved successfully by {viewer.username}")
            UKSAuditLogger.info(f"{viewer.username} | GET_USER_DETAIL | retrieved {username}")

            return user

        except Exception as ex:
            UKSLogger.error(f"Failed to retrieve user {username} by {viewer.username}: {ex}")
            UKSAuditLogger.info(f"{viewer.username} | GET_USER_DETAIL | failed {username}")
            raise

        finally:
            UKSLogger.debug("User detail retrieval ended...")


# =========================================================
# GET ALL ROLE IN SYSTEM
# =========================================================
class RoleView(APIView):
    """
    Superadmin vidi sve role.
    Admin vidi samo role ispod ili jednak nivoa svoje moći.
    """
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        UKSLogger.debug("Role list retrieval started...")
        user = request.user

        try:
            roles = Group.objects.all()

            if user.is_admin() and not user.is_superadmin:
                roles = roles.exclude(name="Superadmin")

            role_names = list(roles.values_list("name", flat=True))

            UKSLogger.info(f"Roles retrieved successfully by {user.username}: {role_names}")
            return Response({"roles": role_names})

        except Exception as ex:
            UKSLogger.error(f"Failed to retrieve roles for {user.username}: {ex}")
            raise

        finally:
            UKSLogger.debug("Role list retrieval ended...")

    """
    Menjanje role korisnika.
    Samo admin (ili superadmin) može menjati role.
    """
    def post(self, request):
        UKSLogger.debug("Role update started...")
        user = request.user
        target_username = request.data.get("username")
        new_role_name = request.data.get("new_role")

        try:
            if not (user.is_admin() or user.is_superadmin):
                UKSLogger.warning(f"Unauthorized role update attempt by {user.username}")
                return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

            if not target_username or not new_role_name:
                UKSLogger.warning(f"Role update failed: missing fields by {user.username}")
                return Response({"message": "Username and role are required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                target_user = User.objects.get(username=target_username)
            except User.DoesNotExist:
                UKSLogger.error(f"Role update failed: user '{target_username}' not found by {user.username}")
                return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            try:
                new_role = Group.objects.get(name=new_role_name)
            except Group.DoesNotExist:
                UKSLogger.error(f"Role update failed: role '{new_role_name}' not found by {user.username}")
                return Response({"message": "Role not found."}, status=status.HTTP_404_NOT_FOUND)

            # Admin ne može da dodeli role iznad svoje moći
            if user.is_admin() and not user.is_superadmin and new_role.name == "Superadmin":
                UKSLogger.warning(f"{user.username} tried to assign Superadmin role, forbidden")
                return Response({"message": "Cannot assign role above your level."}, status=status.HTTP_403_FORBIDDEN)

            # Update role
            target_user.groups.clear()
            target_user.groups.add(new_role)
            target_user.save()

            UKSLogger.info(f"{user.username} updated role for {target_username} to {new_role_name}")
            UKSAuditLogger.info(f"{user.username} | UPDATE_ROLE | set {target_username} role to {new_role_name}")

            return Response(
                {"status": "successful", "message": f"Role updated to {new_role_name} for user {target_username}."}
            )

        except Exception as ex:
            UKSLogger.error(f"Unexpected error during role update by {user.username}: {ex}")
            UKSAuditLogger.info(f"{user.username} | UPDATE_ROLE | failed {target_username}")
            raise

        finally:
            UKSLogger.debug("Role update ended...")


# =========================================================
# CREATE NEW PASSWORD (SUPERADMIN ONLY)
# =========================================================
class GenerateUserPasswordView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        UKSLogger.debug("Generate password started...")
        user = request.user

        try:
            serializer = GeneratePasswordSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            password = serializer.save()

            UKSLogger.info(f"{user.username} generated new password successfully")
            UKSAuditLogger.info(f"{user.username} | GENERATE_PASSWORD | success")

            return Response({
                "message": "success",
                "password": password
            }, status=status.HTTP_200_OK)

        except Exception as ex:
            UKSLogger.error(f"{user.username} failed to generate password: {ex}")
            UKSAuditLogger.info(f"{user.username} | GENERATE_PASSWORD | failed")
            raise

        finally:
            UKSLogger.debug("Generate password ended...")
