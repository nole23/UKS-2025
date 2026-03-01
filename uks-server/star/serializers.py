from rest_framework import serializers
from user.models import User
from star.models import Star

class StarUserSerializer(serializers.ModelSerializer):
    starred_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Star
        fields = ['user_id', 'user_username', 'starred_at']

    # dodatna polja za user info
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)