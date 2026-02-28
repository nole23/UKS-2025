"""
URL configuration for uks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from user.views import GenerateUserPasswordView, RoleView, UserDetailView, UserListAllView, UserRegistrationView, CreateAdminView, UserListView, MyTokenObtainPairView, UserProfileDetailView, PersonalTokenListView, UserProfileUpdateView, PersonalTokenCreateView, UserEmailUpdateView, UserPasswordChangeView
from repository.views import RepositoryBadgeUpdateView, RepositoryListView, RepositorySearchView, DockerInfoView, RepositoryDetailView, RepositoryCollaboratorView
from star.views import StarRepositoryView, StarredRepositoriesView
from pull.views import PullRepositoryView
from tag.views import RepositoryTagListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', UserRegistrationView.as_view(), name='register'),
    path('api/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/profile/', UserProfileDetailView.as_view(), name='profile-detail'),
    path('api/profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('api/profile/email/', UserEmailUpdateView.as_view(), name='profile-email-update'),
    path('api/profile/password/', UserPasswordChangeView.as_view(), name='profile-password-change'),
    path('api/profile/generate-password/', GenerateUserPasswordView.as_view(), name='reset-password'),
    path("api/profile/search/", UserListView.as_view(), name="user-list"),
    path("api/profile/create-admin", CreateAdminView.as_view(), name="create-admin-view"),
    path("api/profile/users/", UserListAllView.as_view(), name="user-list-all"),
    path("api/profile/users/<str:username>/", UserDetailView.as_view(), name="user-detail-view"),
    path("api/profile/roles/", RoleView.as_view(), name="role-list-all"),
    path('api/personal-tokens/', PersonalTokenCreateView.as_view(), name='personal-tokens'),
    path('api/personal-tokens/list/', PersonalTokenListView.as_view(), name='personal-tokens-list'),
    path("api/repositories", RepositoryListView.as_view(), name='repository-list'),
    path("api/repositories/search/", RepositorySearchView.as_view(), name='repository-search'),
    path("api/docker/info", DockerInfoView.as_view()),
    path("api/repositories/<int:pk>/", RepositoryDetailView.as_view()),
    path("api/repositories/<int:pk>/star/", StarRepositoryView.as_view()),
    path("api/repositories/starred/", StarredRepositoriesView.as_view()),
    path("api/repositories/<int:pk>/pull/", PullRepositoryView.as_view(), name="repository-pull"),
    path("api/repositories/<int:pk>/pulls/", PullRepositoryView.as_view(), name="repository-pulls"),
    path("api/repositories/<int:pk>/collaborators/", RepositoryCollaboratorView.as_view()),
    path("api/repositories/<int:pk>/collaborators/<int:user_id>/", RepositoryCollaboratorView.as_view()),
    path("api/repositories/<int:pk>/tags/", RepositoryTagListView.as_view()),
    path("api/repositories/<int:repo_id>/tags/<int:tag_id>/", RepositoryTagListView.as_view()),
    path("api/repositories/<int:pk>/badge/", RepositoryBadgeUpdateView.as_view(), name="update-badget"),
]
