from unittest import TestCase
from unittest.mock import MagicMock, patch
from rest_framework import status
from .views import PullRepositoryView
from repository.models import Repository
from .models import Pull


class PullRepositoryViewUnitTests(TestCase):

    # -------------------
    # POST metoda - pozitivni slučaj
    # -------------------
    @patch("pull.views.Pull.objects")
    @patch("repository.views.Repository.objects")
    def test_post_pull_positive(self, mock_repo_objects, mock_pull_objects):
        # Mock repository koji postoji
        mock_repo = MagicMock()
        mock_repo.pulls_count = 5
        mock_repo_objects.get.return_value = mock_repo

        request = MagicMock()
        request.user = "fake_user"

        view = PullRepositoryView()
        response = view.post(request, pk=1)

        # Proveravamo status i poruku
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == {"message": "Pulled successfully"}

        # Proveravamo da je Pull.objects.create pozvan
        mock_pull_objects.create.assert_called_once_with(repository=mock_repo)
        # Proveravamo da je repo.pulls_count uvećan i sačuvan
        assert mock_repo.pulls_count == 6
        mock_repo.save.assert_called_once_with(update_fields=["pulls_count"])

    # -------------------
    # POST metoda - negativni slučaj (repo ne postoji)
    # -------------------
    @patch("repository.views.Repository.objects")
    def test_post_pull_negative_repository_not_found(self, mock_repo_objects):
        # Simuliramo da repo ne postoji
        mock_repo_objects.get.side_effect = Repository.DoesNotExist

        request = MagicMock()
        request.user = "fake_user"

        view = PullRepositoryView()
        response = view.post(request, pk=999)

        # Proveravamo status i poruku
        assert response.status_code == 404
        assert response.data == {"error": "Repository not found"}

    @patch("pull.views.Pull.objects")
    def test_get_pulls_positive(self, mock_pull_objects):
        # Kreiramo mock QuerySet
        mock_queryset = MagicMock()
        mock_pull_objects.filter.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset

        # Kreiramo nekoliko mock Pull objekata
        pull1 = MagicMock()
        pull1.id = 1
        pull1.pulled_at = "2026-01-25T12:00:00Z"

        pull2 = MagicMock()
        pull2.id = 2
        pull2.pulled_at = "2026-01-24T12:00:00Z"

        # Simuliramo da QuerySet vraća ove objekte
        mock_queryset.__iter__.return_value = [pull1, pull2]

        request = MagicMock()
        request.user = "fake_user"

        view = PullRepositoryView()
        response = view.get(request, pk=1)

        # Proveravamo status i podatke
        assert response.status_code == status.HTTP_200_OK
        assert response.data == [
            {"id": 1, "pulled_at": "2026-01-25T12:00:00Z"},
            {"id": 2, "pulled_at": "2026-01-24T12:00:00Z"},
        ]

        # Proveravamo da su filter i order_by pozvani
        mock_pull_objects.filter.assert_called_once_with(repository_id=1)
        mock_queryset.order_by.assert_called_once_with("-pulled_at")

