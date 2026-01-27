from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Create your views here.
from star.models import Star
from repository.models import Repository
from repository.serializer import RepositorySerializer

class StarRepositoryView(APIView):
    permission_classes = [IsAuthenticated]

    """
    url: api/repositories/4/star/
    requst: Body prazan
    """
    def post(self, request, pk):
        repo = Repository.objects.get(pk=pk)
        Star.objects.get_or_create(user=request.user, repository=repo)
        repo.stars_count += 1
        repo.save()
        return Response({"message": "Starred"})

    """
    url: api/repositories/4/star/
    request: Body prazan
    """
    def delete(self, request, pk):
        repo = Repository.objects.get(pk=pk)
        Star.objects.filter(user=request.user, repository=repo).delete()
        repo.stars_count = max(0, repo.stars_count - 1)
        repo.save()
        return Response({"message": "Unstarred"})

class StarredRepositoriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repos = Repository.objects.filter(stars__user=request.user)
        serializer = RepositorySerializer(repos, many=True)
        return Response(serializer.data)
