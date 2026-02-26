from rest_framework import serializers
from user.models import User, UserProfile, PersonalToken
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import secrets
User = get_user_model()


# --------- User Registration ---------
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        user.set_password(validated_data['password'])
        user.save()

        # default role
        group = Group.objects.get(name="OrdinaryUser")
        user.groups.add(group)

        return user


# --------- User Profile Detail ---------
class UserProfileDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")
    email = serializers.EmailField(source="user.email")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    projects = serializers.SerializerMethodField()
    default_repository = serializers.BooleanField()

    class Meta:
        model = UserProfile
        fields = ("username", "email", "first_name", "last_name", "bio", "avatar",
                  "company_name", "company_email", "company_website", "company_location",
                  "projects", "default_repository")

    def get_projects(self, obj):
        from repository.models import Repository
        repos = Repository.objects.filter(owner=obj.user)
        return [{"name": r.name, "visibility": r.visibility} for r in repos]


# --------- User Profile Update ---------
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", required=False)
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)

    class Meta:
        model = UserProfile
        fields = (
            "first_name", "last_name", "bio", "avatar",
            "company_name", "company_email", "company_website", "company_location", "email",
            "default_repository"
        )

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})

        # Provera email-a
        new_email = user_data.get("email")
        if new_email and User.objects.exclude(pk=instance.user.pk).filter(email=new_email).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})

        # Update user polja
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)

        # Update UserProfile polja
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.user.save()
        instance.save()
        return instance


# --------- Email Update ---------
class UserEmailUpdateSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    old_email = serializers.EmailField()

    def validate(self, attrs):
        user = self.context["request"].user

        # Provera da li se old_email poklapa
        if user.email != attrs["old_email"]:
            raise serializers.ValidationError({"messages": "Old email does not match"})

        # Provera da li je new_email već zauzet kod nekog drugog korisnika
        if User.objects.exclude(pk=user.pk).filter(email=attrs["new_email"]).exists():
            raise serializers.ValidationError({"messages": "This email is already in use"})

        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.email = self.validated_data["new_email"]
        user.save()
        return user


# --------- Password Change ---------
class UserPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        return user


# --------- Personal Access Tokens ---------
class PersonalTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalToken
        fields = ("id", "name", "token", "expires_at", "created_at")
        read_only_fields = ("token", "created_at")


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username")  # samo ovo

# --------- List User with roles -----------
class UserListWithRolesSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "roles")

    def get_roles(self, obj):
        return list(obj.groups.values_list("name", flat=True))


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "bio",
            "avatar",
            "company_name",
            "company_email",
            "company_location",
            "company_website",
            "default_repository"
        )


# --------- User details -------------------
class UserDetailSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "profile"
        ]

    def get_role(self, obj):
        return obj.groups.first().name if obj.groups.exists() else None


class UserDetailSuperSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "last_login",
            "date_joined",
            "is_active",
            "is_staff",
            "groups",
            "permissions",
            "profile"
        ]

    def get_role(self, obj):
        return obj.groups.first().name if obj.groups.exists() else None

    def get_groups(self, obj):
        return [g.name for g in obj.groups.all()]

    def get_permissions(self, obj):
        return list(obj.user_permissions.values_list("codename", flat=True))


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
        if self.user.must_change_password:
            data["must_change_password"] = True

        user = self.user
        profile = getattr(user, "profile", None)

        # dodajemo dodatne informacije o useru u response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            # PROFILE DATA
            "profile": {
                "bio": profile.bio if profile else "",
                "avatar": profile.avatar.url if profile and profile.avatar else None,
                "company_name": profile.company_name if profile else "",
                "company_email": profile.company_email if profile else "",
                "company_location": profile.company_location if profile else "",
                "company_website": profile.company_website if profile else "",
                "default_repository": profile.default_repository if profile else "",
            }
        }
        data['roles'] = list(user.groups.values_list("name", flat=True))
        data['permissions'] = list(user.get_all_permissions())

        return data


class GeneratePasswordSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, value):
        try:
            user = User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        self.user_obj = user
        return value

    def save(self):
        user = self.user_obj

        password = secrets.token_urlsafe(6)

        user.set_password(password)
        user.must_change_password = True

        user.save()

        return password