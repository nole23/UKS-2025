from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Pull
from repository.models import Repository
from utils.logger import UKSLogger, UKSAuditLogger


class PullRepositoryView(APIView):
    permission_classes = [IsAuthenticated]

    """
    POST  /api/repositories/<pk>/pull/
    GET   /api/repositories/<pk>/pulls/
    """
    def post(self, request, pk):
        UKSLogger.debug(f"PullRepositoryView.post started for repo_id={pk}")
        user = request.user
        try:
            try:
                repo = Repository.objects.get(pk=pk)
            except Repository.DoesNotExist:
                UKSLogger.warning(f"{user.username} tried to pull non-existent repository id={pk}")
                UKSAuditLogger.info(f"{user.username} | PULL_REPOSITORY_FAILED | repo_id={pk} | reason=not_found")
                return Response({"error": "Repository not found"}, status=status.HTTP_404_NOT_FOUND)

            Pull.objects.create(repository=repo)
            repo.pulls_count += 1
            repo.save(update_fields=["pulls_count"])
            cache.delete(f"repo_{pk}")

            UKSLogger.info(f"{user.username} pulled repository '{repo.name}' successfully")
            UKSAuditLogger.info(f"{user.username} | PULL_REPOSITORY | repo_id={pk} | repo_name={repo.name}")
            return Response({"message": "Pulled successfully"}, status=status.HTTP_201_CREATED)

        except Exception as ex:
            UKSLogger.error(f"Unexpected error during pulling repository id={pk} by {user.username}: {ex}")
            UKSAuditLogger.info(f"{user.username} | PULL_REPOSITORY_FAILED | repo_id={pk} | error={ex}")
            raise
        finally:
            UKSLogger.debug(f"PullRepositoryView.post ended for repo_id={pk}")

    def get(self, request, pk):
        UKSLogger.debug(f"PullRepositoryView.get started for repo_id={pk}")
        user = request.user
        try:
            pulls = Pull.objects.filter(repository_id=pk).order_by("-pulled_at")
            pull_data = [{"id": p.id, "pulled_at": p.pulled_at} for p in pulls]

            UKSLogger.info(f"{user.username} retrieved pull list for repo_id={pk} (count={len(pull_data)})")
            UKSAuditLogger.info(f"{user.username} | LIST_PULLS | repo_id={pk} | count={len(pull_data)}")
            return Response(pull_data)
        except Exception as ex:
            UKSLogger.error(f"Failed to list pulls for repo_id={pk} by {user.username}: {ex}")
            UKSAuditLogger.info(f"{user.username} | LIST_PULLS_FAILED | repo_id={pk} | error={ex}")
            raise
        finally:
            UKSLogger.debug(f"PullRepositoryView.get ended for repo_id={pk}")