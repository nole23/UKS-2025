from rest_framework import generics, status
from rest_framework.response import Response
from user.serializers import UserRegistrationSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.permissions import AllowAny

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

        # dodajemo dodatne informacije o useru u response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            # 'organization': self.user.organization.name,
            # po želji dodati još info
        }
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]  # <-- ovo omogućava pristup svima
    
