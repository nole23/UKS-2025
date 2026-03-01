from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import Tag
from repository.models import Repository
from utils.logger import UKSAuditLogger, UKSLogger


class RepositoryTagListView(APIView):
    permission_classes = [IsAuthenticated]

    # =========================================================
    # GET  /api/repositories/<pk>/tags/
    # =========================================================
    def get(self, request, pk):
        UKSLogger.debug("RepositoryTagListView.get started...")
        try:
            cache_key = f"repo_tags_{pk}"
            tags_data = cache.get(cache_key)
            if not tags_data:
                tags = Tag.objects.filter(repository_id=pk).order_by("-updated_at")
                tags_data = [
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
                ]
                cache.set(cache_key, tags_data, 300)
                UKSLogger.info(f"Cache populated for repo_tags_{pk}")
            else:
                UKSLogger.info(f"Cache hit for repo_tags_{pk}")

            return Response(tags_data)
        except Exception as ex:
            UKSLogger.error(f"Failed to get tags for repo {pk}: {ex}")
            raise
        finally:
            UKSLogger.debug("RepositoryTagListView.get ended...")


    # =========================================================
    # POST /api/repositories/<pk>/tags/
    # =========================================================
    def post(self, request, pk):
        UKSLogger.debug("RepositoryTagListView.post started...")
        viewer = request.user
        try:
            try:
                repo = Repository.objects.get(pk=pk)
            except Repository.DoesNotExist:
                UKSLogger.warning(f"Repository {pk} not found for user {viewer.username}")
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

            cache.delete(f"repo_tags_{pk}")
            cache.delete(f"repo_{pk}")

            UKSLogger.info(f"Tag {tag.name} created for repo {repo.id} by {viewer.username}")
            UKSAuditLogger.info(f"{viewer.username} | CREATE_TAG | repo_id={repo.id} | tag_id={tag.id}")

            return Response({
                "id": tag.id,
                "name": tag.name,
                "digest": tag.digest,
                "compressed_size_mb": tag.compressed_size_mb,
                "os_arch": tag.os_arch
            }, status=201)
        except Exception as ex:
            UKSLogger.error(f"Failed to create tag for repo {pk}: {ex}")
            UKSAuditLogger.info(f"{viewer.username} | CREATE_TAG_FAILED | repo_id={pk} | error={ex}")
            raise
        finally:
            UKSLogger.debug("RepositoryTagListView.post ended...")


    # =========================================================
    # DELETE /api/repositories/<repo_id>/tags/<tag_id>/
    # =========================================================
    def delete(self, request, repo_id, tag_id):
        UKSLogger.debug("RepositoryTagListView.delete started...")
        viewer = request.user
        try:
            try:
                tag = Tag.objects.get(id=tag_id, repository_id=repo_id)
            except Tag.DoesNotExist:
                UKSLogger.warning(f"Tag {tag_id} not found in repo {repo_id} by {viewer.username}")
                return Response({"error": "Tag not found"}, status=404)

            tag.delete()

            repo = tag.repository
            last_tag = Tag.objects.filter(repository=repo).order_by("-updated_at").first()
            repo.last_pushed_at = last_tag.updated_at if last_tag else None
            repo.save(update_fields=["last_pushed_at"])

            cache.delete(f"repo_tags_{repo_id}")
            cache.delete(f"repo_{repo_id}")
            cache.delete_pattern("all_public_repos*")
            cache.delete_pattern("search_*")

            UKSLogger.info(f"Tag {tag_id} deleted from repo {repo_id} by {viewer.username}")
            UKSAuditLogger.info(f"{viewer.username} | DELETE_TAG | repo_id={repo_id} | tag_id={tag_id}")

            return Response({"message": "Tag deleted"}, status=200)
        except Exception as ex:
            UKSLogger.error(f"Failed to delete tag {tag_id} from repo {repo_id}: {ex}")
            UKSAuditLogger.info(f"{viewer.username} | DELETE_TAG_FAILED | repo_id={repo_id} | tag_id={tag_id} | error={ex}")
            raise
        finally:
            UKSLogger.debug("RepositoryTagListView.delete ended...")