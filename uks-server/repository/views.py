from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import status
from django.db.models import F, Q, Case, IntegerField, Value, When
from django.db.models.functions import Random  # za random redosled
import hashlib

from .models import Repository, RepositoryCollaborator
from .serializer import RepositorySerializer
from Organization.models import Organization
from user.models import User
from user.permissions import IsSuperAdmin
from utils.logger import UKSLogger, UKSAuditLogger

ALL_PUBLIC_REPOS_PATTERN  = "all_public_repos"
REPO_PATTERN = "repo"

# Helper za sigurnu brisanje patterna
def safe_delete_pattern(pattern):
    try:
        cache.delete_pattern(pattern)
    except AttributeError:
        # LocMemCache nema delete_pattern, ignoriši
        pass


class RepositoryListView(APIView):
    permission_classes = [IsAuthenticated]

    """
    Vraca listu svih repositorija na sistemu
    """
    def get(self, request):
        UKSLogger.debug("RepositoryListView.get started...")
        user = request.user
        query = request.query_params.get('q', '')
        cache_key = f"{ALL_PUBLIC_REPOS_PATTERN}_{query}"
        try:
            repos_data = cache.get(cache_key)
            if not repos_data:
                repositories = Repository.objects.filter(visibility="public").order_by("-created_at")
                serializer = RepositorySerializer(repositories, many=True)
                repos_data = serializer.data
                cache.set(cache_key, repos_data, 300)
            UKSLogger.info(f"{user.username} retrieved public repository list (query='{query}')")
            UKSAuditLogger.info(f"{user.username} | LIST_PUBLIC_REPOSITORIES | query='{query}' | count={len(repos_data)}")
            return Response(repos_data)
        except Exception as ex:
            UKSLogger.error(f"Failed to list repositories for {user.username}: {ex}")
            UKSAuditLogger.info(f"{user.username} | LIST_PUBLIC_REPOSITORIES_FAILED | error={ex}")
            raise
        finally:
            UKSLogger.debug("RepositoryListView.get ended...")

    """
    Generise novi repository
    Body: {
        "name": "",
        "description": "",
        "visibility": "",
        "organization_id": "" -> optciono
    }
    """
    def post(self, request):
        UKSLogger.debug("RepositoryListView.post started...")
        user = request.user
        data = request.data.copy()
        org_id = data.get("organization_id")
        organization = None
        try:
            if org_id:
                try:
                    organization = Organization.objects.get(id=org_id)
                except Organization.DoesNotExist:
                    UKSLogger.warning(f"{user.username} tried to create repository with non-existent organization_id={org_id}")
                    UKSAuditLogger.info(f"{user.username} | CREATE_REPOSITORY_FAILED | organization_id={org_id} | reason=not_found")
                    return Response({"error": "Organization not found"}, status=status.HTTP_400_BAD_REQUEST)

            # Odredi badge
            if user.is_superadmin and data.get("badge") == "OFFICIAL":
                badge_value = "OFFICIAL"
            elif data.get("badge") in ["VERIFIED", "SPONSORED"]:
                badge_value = data.get("badge")
            else:
                badge_value = "NONE"

            # Prefix ime korisnika za obične repozitorijume (ako nema org)
            if not organization:
                data["name"] = f"{user.username}/{data.get('name', '')}"
            data["badge"] = badge_value

            serializer = RepositorySerializer(data=data)
            if serializer.is_valid():
                serializer.save(
                    owner=user if not organization else None,
                    organization=organization,
                    badge=badge_value
                )

                safe_delete_pattern(f"{ALL_PUBLIC_REPOS_PATTERN}*")
                safe_delete_pattern("search_*")

                UKSLogger.info(f"Repository '{data.get('name')}' created by {user.username} (badge={badge_value})")
                UKSAuditLogger.info(f"{user.username} | CREATE_REPOSITORY | repo_name={data.get('name')} | badge={badge_value}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            else:
                UKSLogger.warning(f"{user.username} failed to create repository due to validation errors: {serializer.errors}")
                UKSAuditLogger.info(f"{user.username} | CREATE_REPOSITORY_FAILED | errors={serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            UKSLogger.error(f"Unexpected error creating repository for {user.username}: {ex}")
            UKSAuditLogger.info(f"{user.username} | CREATE_REPOSITORY_FAILED | error={ex}")
            raise
        finally:
            UKSLogger.debug("RepositoryListView.post ended...")


class RepositorySearchView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def make_cache_key(self, user, query, visibility, sorting, badges):
        UKSLogger.debug("RepositorySearchView.make_cache_key started...")
        collaborator_ids = list(
            RepositoryCollaborator.objects.filter(user=user).values_list('repository_id', flat=True)
        )
        key_string = f"{user.id}|{query}|{visibility}|{sorting}|{','.join(badges)}|{','.join(map(str, collaborator_ids))}"
        key_hash = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        cache_key = f"repo_search_{key_hash}"
        UKSLogger.debug("RepositorySearchView.make_cache_key ended...")
        return cache_key

    def get_queryset(self, user, query, visibility, sorting, badges):
        UKSLogger.debug("RepositorySearchView.get_queryset started...")
        try:
            if user.is_superadmin:
                qs = Repository.objects.all()
            elif user.is_admin():
                qs = Repository.objects.filter(visibility="public")
            else:
                qs = Repository.objects.filter(
                    Q(visibility="public") |
                    Q(owner=user) |
                    Q(collaborators__user=user)
                )

            if visibility != "all":
                qs = qs.filter(visibility=visibility)
            if badges:
                qs = qs.filter(badge__in=badges)

            if query:
                qs = qs.filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query) |
                    Q(owner__username__icontains=query) |
                    Q(organization__name__icontains=query)
                ).annotate(
                    relevance=Case(When(name__iexact=query, then=Value(50)), default=Value(0), output_field=IntegerField()) +
                              Case(When(name__icontains=query, then=Value(10)), default=Value(0), output_field=IntegerField()) +
                              Case(When(description__icontains=query, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                              Case(When(owner__username__icontains=query, then=Value(3)), default=Value(0), output_field=IntegerField()) +
                              Case(When(organization__name__icontains=query, then=Value(2)), default=Value(0), output_field=IntegerField()) +
                              Case(When(badge="OFFICIAL", then=Value(15)), default=Value(0), output_field=IntegerField()) +
                              Case(When(badge="VERIFIED", then=Value(10)), default=Value(0), output_field=IntegerField()) +
                              Case(When(badge="SPONSORED", then=Value(8)), default=Value(0), output_field=IntegerField()) +
                              F("stars_count") * 2
                ).order_by("-relevance", "-stars_count", "-created_at")
            else:
                if sorting == "random":
                    qs = qs.order_by(Random())
                elif sorting == "oldest":
                    qs = qs.order_by("created_at")
                else:
                    qs = qs.order_by("-created_at")

            qs = qs.select_related("owner", "organization").prefetch_related("collaborators__user")
            UKSLogger.info(f"{user.username} | SEARCH_REPOSITORIES | query='{query}' | visibility='{visibility}' | badges={badges} | count={qs.count()}")
            UKSAuditLogger.info(f"{user.username} | SEARCH_REPOSITORIES | query='{query}' | visibility='{visibility}' | badges={badges} | count={qs.count()}")
            return qs
        except Exception as ex:
            UKSLogger.error(f"Repository search failed for {user.username}: {ex}")
            UKSAuditLogger.info(f"{user.username} | SEARCH_REPOSITORIES_FAILED | error={ex}")
            raise
        finally:
            UKSLogger.debug("RepositorySearchView.get_queryset ended...")

    def get(self, request):
        UKSLogger.debug("RepositorySearchView.get started...")
        try:
            user = request.user
            query = request.query_params.get("q", "")
            visibility = request.query_params.get("visibility", "all")
            sorting = request.query_params.get("sorting", "latest")
            badges = request.query_params.getlist("badge")
            cache_key = self.make_cache_key(user, query, visibility, sorting, badges)
            cached = cache.get(cache_key)
            if cached:
                UKSLogger.info(f"{user.username} retrieved cached search results (query='{query}')")
                return Response(cached)

            qs = self.get_queryset(user, query, visibility, sorting, badges)
            paginator = LimitOffsetPagination()
            page = paginator.paginate_queryset(qs, request)
            data = RepositorySerializer(page if page is not None else qs, many=True).data
            cache.set(cache_key, data, timeout=300)
            return paginator.get_paginated_response(data) if page is not None else Response(data)
        finally:
            UKSLogger.debug("RepositorySearchView.get ended...")
    

class DockerInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "application": "DockerHub Clone",
            "description": "Platform for managing container repositories",
            "features": [
                "Repositories",
                "Organizations",
                "Tags",
                "Pulls",
                "Stars"
            ]
        })


class RepositoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        UKSLogger.debug("RepositoryDetailView.get started...")
        user = request.user
        cache_key = f"{REPO_PATTERN}_{pk}"
        try:
            repo_data = cache.get(cache_key)
            if not repo_data:
                try:
                    repo = Repository.objects.get(pk=pk)
                except Repository.DoesNotExist:
                    UKSLogger.warning(f"{user.username} tried to access non-existent repo_id={pk}")
                    UKSAuditLogger.info(f"{user.username} | ACCESS_REPOSITORY_FAILED | repo_id={pk} | reason=not_found")
                    return Response({"error": "Repository not found"}, status=status.HTTP_404_NOT_FOUND)
                serializer = RepositorySerializer(repo)
                repo_data = serializer.data
                cache.set(cache_key, repo_data, 300)

            UKSLogger.info(f"{user.username} accessed repository repo_id={pk}")
            UKSAuditLogger.info(f"{user.username} | ACCESS_REPOSITORY | repo_id={pk}")
            return Response(repo_data)
        finally:
            UKSLogger.debug("RepositoryDetailView.get ended...")

    def delete(self, request, pk):
        UKSLogger.debug("RepositoryDetailView.delete started...")
        user = request.user
        try:
            repo = Repository.objects.get(pk=pk)
            if repo.owner != user and not user.groups.filter(name="Superadmin").exists():
                UKSLogger.warning(f"{user.username} forbidden to delete repo_id={pk}")
                return Response(status=status.HTTP_403_FORBIDDEN)
            repo.delete()
            safe_delete_pattern(f"{ALL_PUBLIC_REPOS_PATTERN}*")
            safe_delete_pattern("search_*")
            cache.delete(f"{REPO_PATTERN}_{pk}")
            UKSLogger.info(f"{user.username} deleted repository repo_id={pk}")
            UKSAuditLogger.info(f"{user.username} | DELETE_REPOSITORY | repo_id={pk}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        finally:
            UKSLogger.debug("RepositoryDetailView.delete ended...")


class RepositoryCollaboratorView(APIView):
    permission_classes = [IsAuthenticated]

    """
    url: api/repositories/4/collaborators/
    requst: Body prazan
    """
    def get(self, request, pk):
        UKSLogger.debug("RepositoryCollaboratorView.get started...")
        user = request.user
        try:
            collaborators = RepositoryCollaborator.objects.filter(repository_id=pk)
            data = [{"id": c.user.id, "username": c.user.username} for c in collaborators]
            UKSLogger.info(f"{user.username} accessed collaborators for repo_id={pk}")
            UKSAuditLogger.info(f"{user.username} | ACCESS_COLLABORATORS | repo_id={pk} | count={len(data)}")
            return Response(data)
        except Exception as ex:
            UKSLogger.error(f"{user.username} failed to get collaborators for repo_id={pk}: {ex}")
            UKSAuditLogger.info(f"{user.username} | ACCESS_COLLABORATORS_FAILED | repo_id={pk} | error={ex}")
            raise
        finally:
            UKSLogger.debug("RepositoryCollaboratorView.get ended...")

    """
    url: api/repositories/4/collaborators/
    requst:
    {
        "user_id": ,
        "role": "write"
    }
    """
    def post(self, request, pk):
        UKSLogger.debug("RepositoryCollaboratorView.post started...")
        user = request.user
        try:
            repo = Repository.objects.get(pk=pk)
            if repo.owner != user and not user.groups.filter(name="Superadmin").exists():
                UKSLogger.warning(f"{user.username} forbidden to add collaborator to repo_id={pk}")
                return Response(status=status.HTTP_403_FORBIDDEN)

            user_id = request.data.get("user_id")
            try:
                collaborator = User.objects.get(id=user_id)
            except User.DoesNotExist:
                UKSLogger.warning(f"{user.username} tried to add non-existent user_id={user_id} as collaborator to repo_id={pk}")
                UKSAuditLogger.info(f"{user.username} | ADD_COLLABORATOR_FAILED | repo_id={pk} | user_id={user_id} | reason=not_found")
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            RepositoryCollaborator.objects.get_or_create(repository=repo, user=collaborator)
            UKSLogger.info(f"{user.username} added collaborator user_id={user_id} to repo_id={pk}")
            UKSAuditLogger.info(f"{user.username} | ADD_COLLABORATOR | repo_id={pk} | user_id={user_id}")
            return Response({"message": "Collaborator added"})
        except Exception as ex:
            UKSLogger.error(f"{user.username} failed to add collaborator for repo_id={pk}: {ex}")
            UKSAuditLogger.info(f"{user.username} | ADD_COLLABORATOR_FAILED | repo_id={pk} | error={ex}")
            raise
        finally:
            UKSLogger.debug("RepositoryCollaboratorView.post ended...")

    """
    url: api/repositories/4/collaborators/
    requst: Body prazan
    """
    def delete(self, request, pk, user_id):
        UKSLogger.debug("RepositoryCollaboratorView.delete started...")
        user = request.user
        try:
            repo = Repository.objects.get(pk=pk)
            if repo.owner != user and not user.groups.filter(name="Superadmin").exists():
                UKSLogger.warning(f"{user.username} forbidden to remove collaborator from repo_id={pk}")
                return Response(status=status.HTTP_403_FORBIDDEN)

            RepositoryCollaborator.objects.filter(repository=repo, user_id=user_id).delete()
            UKSLogger.info(f"{user.username} removed collaborator user_id={user_id} from repo_id={pk}")
            UKSAuditLogger.info(f"{user.username} | REMOVE_COLLABORATOR | repo_id={pk} | user_id={user_id}")
            return Response({"message": "Collaborator removed"})
        except Exception as ex:
            UKSLogger.error(f"{user.username} failed to remove collaborator for repo_id={pk}: {ex}")
            UKSAuditLogger.info(f"{user.username} | REMOVE_COLLABORATOR_FAILED | repo_id={pk} | error={ex}")
            raise
        finally:
            UKSLogger.debug("RepositoryCollaboratorView.delete ended...")


class RepositoryBadgeUpdateView(APIView):
    """
    API endpoint za ažuriranje badge-a jednog repository-ja.
    Samo vlasnik repozitorijuma ili superadmin može menjati badge.
    """
    permission_classes = [IsSuperAdmin]

    def patch(self, request, pk):
        UKSLogger.debug("RepositoryBadgeUpdateView.patch started...")
        user = request.user
        try:
            try:
                repo = Repository.objects.get(pk=pk)
            except Repository.DoesNotExist:
                UKSLogger.warning(f"{user.username} tried to update badge for non-existent repo_id={pk}")
                UKSAuditLogger.info(f"{user.username} | UPDATE_BADGE_FAILED | repo_id={pk} | reason=not_found")
                return Response({"error": "Repository not found"}, status=status.HTTP_404_NOT_FOUND)

            if user != repo.owner and not user.is_superadmin:
                UKSLogger.warning(f"{user.username} forbidden to update badge for repo_id={pk}")
                return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

            new_badge = request.data.get("badge")
            valid_badges = ["OFFICIAL", "VERIFIED", "SPONSORED", None]

            if new_badge not in valid_badges:
                UKSLogger.warning(f"{user.username} provided invalid badge value='{new_badge}' for repo_id={pk}")
                return Response({"error": f"Invalid badge, must be one of {valid_badges}"}, status=status.HTTP_400_BAD_REQUEST)

            if new_badge == "OFFICIAL" and not user.is_superadmin:
                UKSLogger.warning(f"{user.username} forbidden to set OFFICIAL badge for repo_id={pk}")
                return Response({"error": "Only superadmin can set OFFICIAL badge"}, status=status.HTTP_403_FORBIDDEN)

            repo.badge = new_badge
            repo.save()
            serializer = RepositorySerializer(repo)
            UKSLogger.info(f"{user.username} updated badge for repo_id={pk} to '{new_badge}'")
            UKSAuditLogger.info(f"{user.username} | UPDATE_BADGE | repo_id={pk} | badge={new_badge}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        finally:
            UKSLogger.debug("RepositoryBadgeUpdateView.patch ended...")