# repository/views.py
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
        query = request.query_params.get('q', '')  # u testovima mora biti string
        cache_key = f"{ALL_PUBLIC_REPOS_PATTERN}_{query}"
        repos_data = cache.get(cache_key)

        if not repos_data:
            repositories = Repository.objects.filter(visibility="public").order_by("-created_at")
            serializer = RepositorySerializer(repositories, many=True)
            repos_data = serializer.data
            cache.set(cache_key, repos_data, 300)

        return Response(repos_data)

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
        data = request.data.copy()
        org_id = data.get("organization_id")
        organization = None
        if org_id:
            try:
                organization = Organization.objects.get(id=org_id)
            except Organization.DoesNotExist:
                return Response({"error": "Organization not found"}, status=status.HTTP_400_BAD_REQUEST)

       # Odredi badge
        if request.user.is_superadmin and data.get("badge") == "OFFICIAL":
            badge_value = "OFFICIAL"
        elif data.get("badge") in ["VERIFIED", "SPONSORED"]:
            badge_value = data.get("badge")
        else:
            badge_value = "NONE"

        # Prefix ime korisnika za obične repozitorijume (ako nema org)
        if not organization:
            data["name"] = f"{request.user.username}/{data.get('name', '')}"

        data["badge"] = badge_value

        serializer = RepositorySerializer(data=data)
        if serializer.is_valid():
            serializer.save(
                owner=request.user if not organization else None,
                organization=organization,
                badge=badge_value
            )

            # očisti keš
            safe_delete_pattern(f"{ALL_PUBLIC_REPOS_PATTERN}*")
            safe_delete_pattern("search_*")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RepositorySearchView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination  # DRF pagination


    def make_cache_key(self, user, query, visibility, sorting, badges):
        collaborator_ids = list(
            RepositoryCollaborator.objects.filter(user=user).values_list('repository_id', flat=True)
        )
        key_string = f"{user.id}|{query}|{visibility}|{sorting}|{','.join(badges)}|{','.join(map(str, collaborator_ids))}"
        key_hash = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        return f"repo_search_{key_hash}"

    def get_queryset(self, user, query, visibility, sorting, badges):
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
                relevance=
                    Case(When(name__iexact=query, then=Value(50)), default=Value(0), output_field=IntegerField()) +
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
        return qs

    def get(self, request):
        user = request.user
        query = request.query_params.get("q", "")
        visibility = request.query_params.get("visibility", "all")
        sorting = request.query_params.get("sorting", "latest")
        badges = request.query_params.getlist("badge")  # ["OFFICIAL", "VERIFIED", "SPONSORED"]

        cache_key = self.make_cache_key(user, query, visibility, sorting, badges)
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        qs = self.get_queryset(user, query, visibility, sorting, badges)

        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(qs, request)
        data = RepositorySerializer(page if page is not None else qs, many=True).data
        cache.set(cache_key, data, timeout=300)

        # Ako paginator uspešno paginira, vrati paginated_response
        if page is not None:
            return paginator.get_paginated_response(data)

        # fallback za slučaj da nije paginirao
        return Response(data)
    

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
        cache_key = f"{REPO_PATTERN}_{pk}"
        repo_data = cache.get(cache_key)
        if not repo_data:
            try:
                repo = Repository.objects.get(pk=pk)
            except Repository.DoesNotExist:
                return Response({"error": "Repository not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = RepositorySerializer(repo)
            repo_data = serializer.data
            cache.set(cache_key, repo_data, 300)

        return Response(repo_data)

    def delete(self, request, pk):
        repo = Repository.objects.get(pk=pk)
        if repo.owner != request.user and not request.user.groups.filter(name="Superadmin").exists():
            return Response(status=status.HTTP_403_FORBIDDEN)
        repo.delete()

        cache.delete(f"{REPO_PATTERN}_{pk}")
        # Sigurno brisanje patterna
        safe_delete_pattern(f"{ALL_PUBLIC_REPOS_PATTERN}*")
        safe_delete_pattern("search_*")
        return Response(status=status.HTTP_204_NO_CONTENT)


class RepositoryCollaboratorView(APIView):
    permission_classes = [IsAuthenticated]

    """
    url: api/repositories/4/collaborators/
    requst: Body prazan
    """
    def get(self, request, pk):
        collaborators = RepositoryCollaborator.objects.filter(repository_id=pk)
        return Response([
            {"id": c.user.id, "username": c.user.username}
            for c in collaborators
        ])

     
    """
    url: api/repositories/4/collaborators/
    requst:
    {
        "user_id": ,
        "role": "write"
    }
    """
    def post(self, request, pk):
        repo = Repository.objects.get(pk=pk)
        if repo.owner != request.user and not request.user.groups.filter(name="Superadmin").exists():
            return Response(status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get("user_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        RepositoryCollaborator.objects.get_or_create(
            repository=repo,
            user=user
        )
        return Response({"message": "Collaborator added"})

    """
    url: api/repositories/4/collaborators/
    requst: Body prazan
    """
    def delete(self, request, pk, user_id):
        repo = Repository.objects.get(pk=pk)
        if repo.owner != request.user and not request.user.groups.filter(name="Superadmin").exists():
            return Response(status=status.HTTP_403_FORBIDDEN)

        RepositoryCollaborator.objects.filter(
            repository=repo,
            user_id=user_id
        ).delete()
        return Response({"message": "Collaborator removed"})


class RepositoryBadgeUpdateView(APIView):
    """
    API endpoint za ažuriranje badge-a jednog repository-ja.
    Samo vlasnik repozitorijuma ili superadmin može menjati badge.
    """
    permission_classes = [IsSuperAdmin]

    def patch(self, request, pk):
        try:
            repo = Repository.objects.get(pk=pk)
        except Repository.DoesNotExist:
            return Response({"error": "Repository not found"}, status=status.HTTP_404_NOT_FOUND)

        # Provera prava
        if request.user != repo.owner and not request.user.is_superadmin:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        # Uzmi novi badge iz request-a
        new_badge = request.data.get("badge")
        valid_badges = ["OFFICIAL", "VERIFIED", "SPONSORED", None]

        if new_badge not in valid_badges:
            return Response({"error": f"Invalid badge, must be one of {valid_badges}"}, status=status.HTTP_400_BAD_REQUEST)

        # Samo superadmin može postaviti OFFICIAL
        if new_badge == "OFFICIAL" and not request.user.is_superadmin:
            return Response({"error": "Only superadmin can set OFFICIAL badge"}, status=status.HTTP_403_FORBIDDEN)

        repo.badge = new_badge
        repo.save()

        serializer = RepositorySerializer(repo)
        return Response(serializer.data, status=status.HTTP_200_OK)