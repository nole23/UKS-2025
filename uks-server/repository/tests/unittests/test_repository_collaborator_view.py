from unittest.mock import MagicMock, patch
from django.test import TestCase
from rest_framework import status
from repository.views import RepositoryCollaboratorView


# -----------------------------
# RepositoryCollaboratorView
# -----------------------------
class RepositoryCollaboratorViewTests(TestCase):

    # -------------------
    # GET metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.RepositoryCollaborator.objects")
    def test_get_collaborators_positive(self, mock_collab_objects):
        collab1 = MagicMock()
        collab1.user.id = 1
        collab1.user.username = "user1"
        collab2 = MagicMock()
        collab2.user.id = 2
        collab2.user.username = "user2"
        mock_collab_objects.filter.return_value = [collab1, collab2]
        request = MagicMock()
        request.user = "fake_user"
        view = RepositoryCollaboratorView()
        response = view.get(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            {"id": 1, "username": "user1"},
            {"id": 2, "username": "user2"},
        ])

    # -------------------
    # POST metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.User.objects")
    @patch("repository.views.Repository.objects")
    def test_post_collaborator_positive(self, mock_repo_objects, mock_user_objects, mock_collab_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "fake_user"
        mock_repo_objects.get.return_value = mock_repo

        mock_user = MagicMock()
        mock_user_objects.get.return_value = mock_user

        mock_collab_objects.get_or_create.return_value = (MagicMock(), True)

        request = MagicMock()
        request.user = "fake_user"
        request.data = {"user_id": 123}

        view = RepositoryCollaboratorView()
        response = view.post(request, pk=1)

        assert response.status_code == 200
        assert response.data == {"message": "Collaborator added"}
        mock_collab_objects.get_or_create.assert_called_once_with(repository=mock_repo, user=mock_user)

    # -------------------
    # POST metoda - negativni slučaj (user nije owner)
    # -------------------
    @patch("repository.views.Repository.objects")
    def test_post_collaborator_forbidden(self, mock_repo_objects):
        mock_repo = MagicMock()
        mock_repo.owner = MagicMock()
        mock_repo_objects.get.return_value = mock_repo

        mock_user = MagicMock()
        mock_user.groups.filter.return_value.exists.return_value = False

        request = MagicMock()
        request.user = mock_user
        request.data = {"user_id": 123}

        view = RepositoryCollaboratorView()
        response = view.post(request, pk=1)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # -------------------
    # DELETE metoda - pozitivni slučaj
    # -------------------
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    def test_delete_collaborator_positive(self, mock_repo_objects, mock_collab_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "fake_user"
        mock_repo_objects.get.return_value = mock_repo

        mock_collab_qs = MagicMock()
        mock_collab_objects.filter.return_value = mock_collab_qs

        request = MagicMock()
        request.user = "fake_user"

        view = RepositoryCollaboratorView()
        response = view.delete(request, pk=1, user_id=123)

        assert response.status_code == 200
        assert response.data == {"message": "Collaborator removed"}
        mock_collab_objects.filter.assert_called_once_with(repository=mock_repo, user_id=123)
        mock_collab_qs.delete.assert_called_once()

    # -------------------
    # DELETE metoda - negativni slučaj (user nije owner)
    # -------------------
    @patch("repository.views.Repository.objects")
    def test_delete_collaborator_forbidden(self, mock_repo_objects):
        mock_repo = MagicMock()
        mock_repo.owner = MagicMock()  # owner nije isti user
        mock_repo_objects.get.return_value = mock_repo

        mock_user = MagicMock()
        mock_user.groups.filter.return_value.exists.return_value = False

        request = MagicMock()
        request.user = mock_user

        view = RepositoryCollaboratorView()
        response = view.delete(request, pk=1, user_id=123)

        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @patch("repository.views.RepositoryCollaborator.objects")
    @patch("repository.views.Repository.objects")
    def test_post_collaborator_superadmin(self, mock_repo_objects, mock_collab_objects):
        mock_repo = MagicMock()
        mock_repo.owner = "other_user"
        mock_repo_objects.get.return_value = mock_repo

        mock_user = MagicMock()
        mock_collab_objects.get_or_create.return_value = (MagicMock(), True)

        request = MagicMock()
        request.user = mock_user
        request.data = {"user_id": 123}

        # Make user superadmin
        mock_user.is_superadmin = True

        with patch("repository.views.User.objects.get", return_value=mock_user):
            view = RepositoryCollaboratorView()
            response = view.post(request, pk=1)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, {"message": "Collaborator added"})
            mock_collab_objects.get_or_create.assert_called_once_with(repository=mock_repo, user=mock_user)

