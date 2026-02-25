# repository/views.py
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.db.models.functions import Random  # za random redosled
import hashlib

from .models import Repository, RepositoryCollaborator
from .serializer import RepositoryCreateSerializer, RepositorySerializer
from Organization.models import Organization
from user.models import User

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

        # Samo superadmin može kreirati official repository
        if request.user.is_superadmin:
            official_flag = data.get("official", False)
        else:
            official_flag = False

        # Prefix ime korisnika za obične repozitorijume (ako nije official)
        if not official_flag and not organization:
            data["name"] = f"{request.user.username}/{data.get('name', '')}"

        data["official"] = official_flag
        
        serializer = RepositorySerializer(data=data)
        if serializer.is_valid():
            print('1')

            serializer.save(
                owner=request.user if not organization else None,
                organization=organization,
                official=official_flag  # <-- postavljanje flega
            )
            safe_delete_pattern(f"{ALL_PUBLIC_REPOS_PATTERN}*")
            safe_delete_pattern("search_*")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RepositorySearchView(APIView):
    permission_classes = [IsAuthenticated]

    def make_cache_key(self, user, query, visibility, sorting):
        """
        Generiše jedinstveni cache key uzimajući u obzir:
        - user ID
        - query string
        - visibility filter
        - sorting filter
        - lista ID-jeva repozitorijuma gde je user collaborator
        """
        # ID-jevi repozitorijuma gde je user collaborator
        collaborator_ids = list(
            RepositoryCollaborator.objects.filter(user=user).values_list('repository_id', flat=True)
        )
        # String za hash
        key_string = f"{user.id}|{query}|{visibility}|{sorting}|{','.join(map(str, collaborator_ids))}"
        # Generišemo MD5 hash da key bude kratak i siguran
        key_hash = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        return f"repo_search_{key_hash}"

    def get(self, request):
        user = request.user
        query = request.query_params.get("q", "")
        visibility = request.query_params.get("visibility", "all")
        sorting = request.query_params.get("sorting", "latest")

        print(user)
        cache_key = self.make_cache_key(user, query, visibility, sorting)
        repos_data = cache.get(cache_key)
        if repos_data:
            return Response(repos_data)

        # ---------- BASE QUERYSET ----------
        if user.is_superadmin:
            qs = Repository.objects.all()

        elif user.is_admin():
            qs = Repository.objects.filter(visibility="public")

        else:
            # Običan user vidi:
            # - svoje repozitorijume (owner)
            # - public repozitorijume
            # - repozitorijume gde je collaborator
            qs = Repository.objects.filter(
                Q(visibility="public") |
                Q(owner=user) |
                Q(collaborators__user=user)   # <-- koristimo reverse FK
            )

        # ---------- VISIBILITY PARAM ----------
        if visibility != "all":
            qs = qs.filter(visibility=visibility)

        # ---------- SEARCH ----------
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(owner__username__icontains=query) |
                Q(organization__name__icontains=query)
            )

        # ---------- SORT ----------
        if sorting == "random":
            qs = qs.order_by(Random())
        elif sorting == "oldest":
            qs = qs.order_by("created_at")
        else:
            qs = qs.order_by("-created_at")

        # ---------- SERIALIZE ----------
        # Prefetch collaborators da se izbegne N+1 problem
        data = RepositorySerializer(qs.prefetch_related("collaborators__user"), many=True).data

        # ---------- CACHE ----------
        cache.set(cache_key, data, timeout=300)

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
            repo = Repository.objects.get(pk=pk)
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

        user = User.objects.get(id=request.data.get("user_id"))
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