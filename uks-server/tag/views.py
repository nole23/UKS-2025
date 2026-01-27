from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import Tag
from repository.models import Repository


class RepositoryTagListView(APIView):
    permission_classes = [IsAuthenticated]

    """
    GET  /api/repositories/<pk>/tags/
    """
    def get(self, request, pk):
        tags = Tag.objects.filter(repository_id=pk).order_by("-updated_at")
        return Response([
            {
                "id": t.id,
                "name": t.name,
                "digest": t.digest,
                "compressed_size_mb": t.compressed_size_mb,
                "os_arch": t.os_arch,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            }
            for t in tags
        ])

    """
    POST /api/repositories/<pk>/tags/
    request: 
    {
        "name": "latest",
        "digest": "sha256:abcd1234",
        "compressed_size_mb": 145,
        "os_arch": "linux/amd64"
    }
    """
    def post(self, request, pk):
        try:
            repo = Repository.objects.get(pk=pk)
        except Repository.DoesNotExist:
            return Response({"error": "Repository not found"}, status=404)

        tag = Tag.objects.create(
            repository=repo,
            name=request.data.get("name"),
            digest=request.data.get("digest"),
            compressed_size_mb=request.data.get("compressed_size_mb"),
            os_arch=request.data.get("os_arch"),
        )

        repo.last_pushed_at = timezone.now()
        repo.save(update_fields=["last_pushed_at"])

        return Response({
            "id": tag.id,
            "name": tag.name,
            "digest": tag.digest,
            "compressed_size_mb": tag.compressed_size_mb,
            "os_arch": tag.os_arch
        }, status=201)
    
    def delete(self, request, repo_id, tag_id):
        try:
            tag = Tag.objects.get(id=tag_id, repository_id=repo_id)
        except Tag.DoesNotExist:
            return Response({"error": "Tag not found"}, status=404)

        tag.delete()

        # Ažuriraj last_pushed_at repoa na najnoviji tag (ako postoji)
        repo = tag.repository
        last_tag = Tag.objects.filter(repository=repo).order_by("-updated_at").first()
        repo.last_pushed_at = last_tag.updated_at if last_tag else None
        repo.save(update_fields=["last_pushed_at"])

        return Response({"message": "Tag deleted"}, status=200)
