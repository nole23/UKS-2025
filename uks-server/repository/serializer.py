# repository/serializers.py
from rest_framework import serializers
from .models import Repository

class RepositorySerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(
        source="owner.username",
        read_only=True
    )
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True
    )

    # Novo polje za prikaz poslednjeg push-a
    last_pushed_at = serializers.DateTimeField(read_only=True)
    
    # Opcionalno: prikaz broja stars i pulls
    stars_count = serializers.IntegerField(read_only=True)
    pulls_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Repository
        fields = [
            "id",
            "name",
            "description",
            "visibility",
            "created_at",
            "owner_username",
            "organization_name",
            "last_pushed_at",  # 👈 dodato
            "stars_count",     # 👈 opcionalno
            "pulls_count",     # 👈 opcionalno
            "official"
        ]


class RepositoryCreateSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(
        source="owner.username", read_only=True
    )
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    # Dodajemo optional field za official
    official = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Repository
        fields = [
            "id",
            "name",
            "description",
            "visibility",
            "organization",
            "owner_username",
            "organization_name",
            "official",
        ]

    def validate(self, attrs):
        user = self.context["request"].user
        official = attrs.pop("official", False)

        # Samo superadmin može da kreira official repository
        if official and not user.is_superadmin:
            raise serializers.ValidationError("Only superadmin can create official repositories.")

        attrs["official"] = official
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        official = validated_data.pop("official", False)
        organization = validated_data.get("organization", None)

        # Ako nije superadmin i nije official, dodaj prefix sa imenom korisnika
        if not official and not user.is_superadmin:
            validated_data["name"] = f"{user.username}_{validated_data['name']}"

        # Postavi owner samo ako nema organizaciju
        if not organization:
            validated_data["owner"] = user

        return super().create(validated_data)