from rest_framework import generics, permissions, status
from rest_framework.response import Response
from user.serializers import (
    UserRegistrationSerializer,
    UserProfileDetailSerializer,
    UserProfileUpdateSerializer,
    UserEmailUpdateSerializer,
    UserPasswordChangeSerializer,
    PersonalTokenSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .models import PersonalToken


# Registration
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": {
                "username": user.username,
                "email": user.email
            },
            "message": "User registered successfully"
        }, status=status.HTTP_201_CREATED)

# Login
"""
request:
{
  "username": "",
  "password": ""
}
reponse:
{
    "refresh": "",
    "access": ""
}
"""
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # optional: add custom claims
        token['username'] = user.username
        return token

    def validate(self, attrs):
        # ovo vraća standardni response sa access i refresh tokenom
        data = super().validate(attrs)

        user = self.user
        profile = getattr(user, "profile", None)

        # dodajemo dodatne informacije o useru u response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            # PROFILE DATA
            "profile": {
                "first_name": profile.first_name if profile else "",
                "last_name": profile.last_name if profile else "",
                "bio": profile.bio if profile else "",
                "avatar": profile.avatar.url if profile and profile.avatar else None,

                "company_name": profile.company_name if profile else "",
                "company_email": profile.company_email if profile else "",
                "company_location": profile.company_location if profile else "",
                "company_website": profile.company_website if profile else "",
            }
        }
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]  # <-- ovo omogućava pristup svima
    

# --------- Profile Detail ---------
class UserProfileDetailView(generics.RetrieveAPIView):
    serializer_class = UserProfileDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


# --------- Profile Update ---------
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
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


# --------- Email Update ---------
"""
PATCH request: 
{
    "old_email": "",
    "new_email": ""
}
"""
class UserEmailUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = UserEmailUpdateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Email updated successfully"}, status=status.HTTP_200_OK)


# --------- Password Change ---------
"""
PATCH request: 
{
    "old_password": "",
    "new_password": ""
}
"""
class UserPasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = UserPasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password changed successfully"})


# Kreiranje tokena
"""
POST request: 
{
    "name": ""
}
"""
class PersonalTokenCreateView(generics.CreateAPIView):
    serializer_class = PersonalTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PersonalTokenListView(generics.ListAPIView):
    serializer_class = PersonalTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # vraća samo tokene za trenutno ulogovanog korisnika
        return PersonalToken.objects.filter(user=self.request.user)