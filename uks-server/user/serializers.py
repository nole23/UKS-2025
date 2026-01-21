from rest_framework import serializers
from user.models import User, UserProfile, PersonalToken
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
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
        validated_data.pop('password2')
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

# --------- User Profile Detail ---------
class UserProfileDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")
    email = serializers.EmailField(source="user.email")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    projects = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ("username", "email", "first_name", "last_name", "bio", "avatar",
                  "company_name", "company_email", "company_website", "company_location",
                  "projects")

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
            "company_name", "company_email", "company_website", "company_location", "email"
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
            raise serializers.ValidationError({"old_email": "Old email does not match"})

        # Provera da li je new_email već zauzet kod nekog drugog korisnika
        if User.objects.exclude(pk=user.pk).filter(email=attrs["new_email"]).exists():
            raise serializers.ValidationError({"new_email": "This email is already in use"})

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
        user.save()
        return user

# --------- Personal Access Tokens ---------
class PersonalTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalToken
        fields = ("id", "name", "token", "expires_at", "created_at")
        read_only_fields = ("token", "created_at")
