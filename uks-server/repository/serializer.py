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
        ]
