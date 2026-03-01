from rest_framework import serializers
from user.models import User, UserProfile, PersonalToken
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import secrets
from utils.logger import UKSAuditLogger, UKSLogger

User = get_user_model()


# --------- User Registration ---------
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')

    def validate(self, attrs):
        UKSLogger.debug("UserRegistrationSerializer.validate started...")
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        UKSLogger.debug("UserRegistrationSerializer.validate ended...")
        return attrs

    def create(self, validated_data):
        UKSLogger.debug("UserRegistrationSerializer.create started...")
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        group = Group.objects.get(name="OrdinaryUser")
        user.groups.add(group)
        UKSLogger.debug("UserRegistrationSerializer.create ended...")
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
        UKSLogger.debug("UserProfileUpdateSerializer.update started...")
        user_data = validated_data.pop("user", {})

        new_email = user_data.get("email")
        if new_email and User.objects.exclude(pk=instance.user.pk).filter(email=new_email).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})

        for attr, value in user_data.items():
            setattr(instance.user, attr, value)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.user.save()
        instance.save()
        UKSLogger.debug("UserProfileUpdateSerializer.update ended...")
        return instance


# --------- Email Update ---------
class UserEmailUpdateSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    old_email = serializers.EmailField()

    def validate(self, attrs):
        UKSLogger.debug("UserEmailUpdateSerializer.validate started...")
        user = self.context["request"].user

        if user.email != attrs["old_email"]:
            raise serializers.ValidationError({"messages": "Old email does not match"})

        if User.objects.exclude(pk=user.pk).filter(email=attrs["new_email"]).exists():
            raise serializers.ValidationError({"messages": "This email is already in use"})

        UKSLogger.debug("UserEmailUpdateSerializer.validate ended...")
        return attrs

    def save(self, **kwargs):
        UKSLogger.debug("UserEmailUpdateSerializer.save started...")
        user = self.context["request"].user
        user.email = self.validated_data["new_email"]
        user.save()
        UKSLogger.debug("UserEmailUpdateSerializer.save ended...")
        return user


# --------- Password Change ---------
class UserPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        UKSLogger.debug("UserPasswordChangeSerializer.validate_old_password started...")
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        UKSLogger.debug("UserPasswordChangeSerializer.validate_old_password ended...")
        return value

    def save(self, **kwargs):
        UKSLogger.debug("UserPasswordChangeSerializer.save started...")
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        UKSLogger.debug("UserPasswordChangeSerializer.save ended...")
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
        UKSLogger.debug("MyTokenObtainPairSerializer.validate started...")
        username = attrs.get("username")
        UKSLogger.debug(f"Authorize for username={username}")

        # ovo vraća standardni response sa access i refresh tokenom
        data = super().validate(attrs)
        user = self.user

        try:
            if self.user.must_change_password:
                UKSLogger.info(f"User {user.username} must change password")
                UKSAuditLogger.info(f"User {user.username} login: must change password")
                data["must_change_password"] = True

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

            UKSLogger.info(f"Login successful for username={user.username}")
            UKSAuditLogger.info(f"User {user.username} logged in successfully")
        except Exception as ex:
            UKSLogger.error(f"Login failed for username={username}: {ex}")
            UKSAuditLogger.info(f"User {username} login failed: {ex}")
            raise

        UKSLogger.debug("MyTokenObtainPairSerializer.validate ended...")
        return data


class GeneratePasswordSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, value):
        UKSLogger.debug("GeneratePasswordSerializer.validate_username started...")
        try:
            user = User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        self.user_obj = user
        UKSLogger.debug("GeneratePasswordSerializer.validate_username ended...")
        return value

    def save(self):
        UKSLogger.debug("GeneratePasswordSerializer.save started...")
        user = self.user_obj
        password = secrets.token_urlsafe(6)
        user.set_password(password)
        user.must_change_password = True
        user.save()
        UKSLogger.debug("GeneratePasswordSerializer.save ended...")
        return password