# repository/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.db.models.functions import Random  # za random redosled

from .models import Repository
from .serializer import RepositorySerializer
from Organization.models import Organization


class RepositoryListView(APIView):
    permission_classes = [IsAuthenticated]

    """
    Vraca listu svih repositorija na sistemu
    """
    def get(self, request):
        query = request.query_params.get('q', '')
        repositories = Repository.objects.filter(
            visibility="public"
        ).order_by("-created_at")
        serializer = RepositorySerializer(repositories, many=True)
        return Response(serializer.data)

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
        data = request.data.copy()  # kopija podataka iz request-a

        # Provera organization_id
        org_id = data.get("organization_id")
        organization = None
        if org_id:
            try:
                organization = Organization.objects.get(id=org_id)
            except Organization.DoesNotExist:
                return Response(
                    {"error": "Organization not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Ako ni owner ni organization nisu postavljeni
        if not organization and not request.user:
            return Response(
                {"error": "Owner or organization must be provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RepositorySerializer(data=data)
        if serializer.is_valid():
            # Sačuvaj repo
            serializer.save(
                owner=request.user if not organization else None,
                organization=organization
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RepositorySearchView(APIView):
    permission_classes = [IsAuthenticated]

    """
    Trazi po owneru, organizaciji, ili nazivu repositorija
    """
    def get(self, request):
        query = request.query_params.get("q", "")
        visibility = request.query_params.get("visibility", "")
        sorting = request.query_params.get("sorting", "")  # 'r', 'l', 'o'

        repositories = Repository.objects.all()

        repositories = Repository.objects.filter(
            Q(name__icontains=query) |
            Q(owner__username__icontains=query) |
            Q(organization__name__icontains=query)
        )

        if visibility in ['public', 'private']:
            repositories = repositories.filter(visibility=visibility)
        
        if sorting == 'r':
            repositories = repositories.order_by(Random())  # nasumično
        elif sorting == 'o':
            repositories = repositories.order_by('created_at')  # oldest
        else:
            # podrazumevano ili 'l'
            repositories = repositories.order_by('-created_at')  # latest
        
        serializer = RepositorySerializer(repositories, many=True)
        return Response(serializer.data)

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
