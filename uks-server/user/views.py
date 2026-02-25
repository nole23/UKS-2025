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
        # --- 1️⃣ Dohvati user podatke ---
        user_data = request.data.get("user", request.data)
        # Ako klijent pošalje samo user dict ili cijeli request

        # --- 2️⃣ Dohvati role ako postoji ---
        role_name = request.data.get("roleName")  # može biti None
        if role_name:
            group, _ = Group.objects.get_or_create(name=role_name)
        else:
            # fallback na default
            is_super = request.data.get("isSuperadmin", False)
            default_group_name = "Superadmin" if is_super else "OrdinaryUser"
            group, _ = Group.objects.get_or_create(name=default_group_name)

        # --- 3️⃣ Serializacija ---
        serializer = self.get_serializer(data=user_data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        user.groups.add(group)
        
        return Response({
            "user": {
                "username": user.username,
                "email": user.email
            },
            "message": "User registered successfully"
        }, status=status.HTTP_201_CREATED)


# =========================================================
# LOGIN
# =========================================================
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]  # <-- ovo omogućava pristup svima
    

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

    def get_object(self):
        """
        Vrati stvarnu instancu modela UserProfile.
        Ovo je obavezno da bi integracioni testovi i DRF serializer radili.
        """
        viewer = self.request.user
        user_id = self.request.query_params.get("user_id")

        if user_id:
            target = get_object_or_404(User, pk=user_id)

            if not AccessPolicy.can_view_user(viewer, target):
                raise PermissionDenied()
            
            return target.profile
        return viewer.profile

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve da podrži keširanje serijalizovanih podataka.
        """
        profile = self.get_object()
        cache_key = f"user_profile_{profile.user_id}"

        profile_data = cache.get(cache_key)
        if not profile_data:
            # Serijalizuj
            serializer = self.get_serializer(profile)
            profile_data = serializer.data
            # Sačuvaj u keš 5 minuta
            cache.set(cache_key, profile_data, 300)

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
        viewer = self.request.user
        user_id = self.request.query_params.get("user_id")

        if user_id:
            target = get_object_or_404(User, pk=user_id)

            if not AccessPolicy.can_view_user(viewer, target):
                raise PermissionDenied()

            return target.profile
        
        return viewer.profile
    
    def perform_update(self, serializer):
        instance = serializer.save()

        # invalidate cache
        cache.delete(f"user_profile_{instance.user.id}")


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
        serializer = UserEmailUpdateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Email updated successfully"}, status=status.HTTP_200_OK)


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
        serializer = UserPasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Password changed successfully"})


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
        if self.request.user.personal_tokens.count() >= 5:
            raise ValidationError("Token limit reached")
        
        serializer.save(user=self.request.user)


# =========================================================
# PERSONAL TOKEN CREATE
# =========================================================
class PersonalTokenListView(generics.ListAPIView):
    serializer_class = PersonalTokenSerializer
    permission_classes = [IsAdminOrSelf]

    def get_queryset(self):
        return PersonalToken.objects.filter(user=self.request.user)
    

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
        qs = AccessPolicy.scope_user_queryset(
                self.request.user,
                User.objects.all()
            )

        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(username__icontains=q)

        return qs


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
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Missing fields"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error":"Username exists"}, status=400)    

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        admin_group = Group.objects.get(name="Administrator")
        user.groups.add(admin_group)

        return Response({"message": "Admin created"})
    

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
        # vraća sve korisnike bez ikakvih filtera
        return User.objects.prefetch_related("groups").exclude(pk=self.request.user.pk)


# =========================================================
# GET ONE USER
# =========================================================
class UserDetailView(RetrieveAPIView):
    permission_classes = [IsAdminOrSelf]
    lookup_field = "username"
    queryset = User.objects.select_related("profile").prefetch_related("groups")

    def get_serializer_class(self):
        if self.request.user.is_superadmin:
            return UserDetailSuperSerializer
        return UserDetailSerializer


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
        user = request.user
        roles = Group.objects.all()

        # admin ne vidi role iznad sebe (npr. Superadmin)
        if user.is_admin() and not user.is_superadmin:
            roles = roles.exclude(name="Superadmin")

        role_names = list(roles.values_list("name", flat=True))
        return Response({"roles": role_names})

    def post(self, request):
        """
        Menjanje role korisnika.
        Samo admin (ili superadmin) može menjati role.
        """
        user = request.user

        if not (user.is_admin() or user.is_superadmin):
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        print(request.data.get("new_role"))
        target_username = request.data.get("username")
        new_role_name = request.data.get("new_role")

        if not target_username or not new_role_name:
            return Response({"message": "Username and role are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = User.objects.get(username=target_username)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            new_role = Group.objects.get(name=new_role_name)
        except Group.DoesNotExist:
            return Response({"message": "Role not found."}, status=status.HTTP_404_NOT_FOUND)

        # Admin ne može da dodeli role iznad svoje moći
        if user.is_admin() and not user.is_superadmin:
            if new_role.name == "Superadmin":
                return Response({"message": "Cannot assign role above your level."}, status=status.HTTP_403_FORBIDDEN)

        # Ukloni sve role korisnika i dodaj novu
        target_user.groups.clear()
        target_user.groups.add(new_role)
        target_user.save()

        return Response({"status": "sucessifull", "message": f"Role updated to {new_role_name} for user {target_username}."})


# =========================================================
# CREATE NEW PASSWORD (SUPERADMIN ONLY)
# =========================================================
class GenerateUserPasswordView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        serializer = GeneratePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.save()

        return Response({
            "message": "success",
            "password": password
        }, status=status.HTTP_200_OK)
        