# repository/serializers.py
from rest_framework import serializers
from .models import Repository
from utils.logger import UKSLogger

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
            "last_pushed_at",
            "stars_count",
            "pulls_count",
            "badge"
        ]
        
    def to_representation(self, instance):
        UKSLogger.debug(f"Serializing repository id={instance.id} name={instance.name}")
        ret = super().to_representation(instance)
        UKSLogger.debug(f"Serialized data for repo_id={instance.id}: {ret}")
        return ret