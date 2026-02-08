from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Pull
from repository.models import Repository


class PullRepositoryView(APIView):
    permission_classes = [IsAuthenticated]

    """
    POST  /api/repositories/<pk>/pull/
    GET   /api/repositories/<pk>/pulls/
    """
    def post(self, request, pk):
        try:
            repo = Repository.objects.get(pk=pk)
        except Repository.DoesNotExist:
            return Response({"error": "Repository not found"}, status=404)

        Pull.objects.create(repository=repo)
        repo.pulls_count += 1
        repo.save(update_fields=["pulls_count"])

        cache.delete(f"repo_{pk}")

        return Response({"message": "Pulled successfully"}, status=201)

    def get(self, request, pk):
        pulls = Pull.objects.filter(repository_id=pk).order_by("-pulled_at")

        return Response([
            {
                "id": p.id,
                "pulled_at": p.pulled_at
            }
            for p in pulls
        ])
