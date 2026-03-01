from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from star.models import Star
from repository.models import Repository
from repository.serializer import RepositorySerializer
from .serializers import StarUserSerializer

class StarRepositoryView(APIView):
    permission_classes = [IsAuthenticated]

    def _invalidate_cache(self, pk: int):
        """Privatna metoda koja čisti keš vezan za repository"""
        try:
            cache.delete(f"repo_{pk}")
            cache.delete(f"repo_tags_{pk}")
            cache.delete(f"repo_stars_{pk}")
            if hasattr(cache, "delete_pattern"):
                cache.delete_pattern("all_public_repos*")
                cache.delete_pattern("search_*")
        except Exception as e:
            # samo loguj, ne prekidaj operaciju
            print(f"Cache invalidation failed: {e}")

    def get(self, request, pk):
        cache_key = f"repo_stars_{pk}"
        cached_users = cache.get(cache_key)
        if cached_users:
            return Response(cached_users)

        try:
            repo = Repository.objects.get(pk=pk)
        except Repository.DoesNotExist:
            return Response({"error": "Repository not found"}, status=404)

        if not (request.user.is_superadmin or request.user.is_admin() or repo.owner == request.user):
            return Response({"error": "Permission denied"}, status=403)

        stars = Star.objects.filter(repository=repo).select_related("user")
        serializer = StarUserSerializer(stars, many=True)
        cache.set(cache_key, serializer.data, 300)
        return Response(serializer.data)

    """
    url: api/repositories/4/star/
    requst: Body prazan
    """
    def post(self, request, pk):
        try:
            repo = Repository.objects.get(pk=pk)
        except Repository.DoesNotExist:
            return Response({"error": "Repository not found"}, status=404)

        with transaction.atomic():
            Star.objects.get_or_create(user=request.user, repository=repo)
            repo.stars_count += 1
            repo.save(update_fields=['stars_count'])

        self._invalidate_cache(pk)

        return Response({"message": "Starred"})

    """
    url: api/repositories/4/star/
    request: Body prazan
    """
    def delete(self, request, pk):
        try:
            repo = Repository.objects.get(pk=pk)
        except Repository.DoesNotExist:
            return Response({"error": "Repository not found"}, status=404)
        
        with transaction.atomic():
            Star.objects.filter(user=request.user, repository=repo).delete()
            repo.stars_count = max(0, repo.stars_count - 1)
            repo.save(update_fields=['stars_count'])

        self._invalidate_cache(pk)

        return Response({"message": "Unstarred"})


class StarredRepositoriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repos = Repository.objects.filter(stars__user=request.user)
        serializer = RepositorySerializer(repos, many=True)
        # keširamo samo podatke, ne ceo serializer
        cache.set(f"repositori_view_{request.user}", serializer.data, 300)
        return Response(serializer.data)