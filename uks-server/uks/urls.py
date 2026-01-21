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
from user.views import UserRegistrationView, MyTokenObtainPairView, UserProfileDetailView, PersonalTokenListView, UserProfileUpdateView, PersonalTokenCreateView, UserEmailUpdateView, UserPasswordChangeView
from repository.views import RepositoryListView, RepositorySearchView, DockerInfoView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', UserRegistrationView.as_view(), name='register'),
    path('api/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/repositories", RepositoryListView.as_view(), name='repository-list'),
    path("api/repositories/search", RepositorySearchView.as_view(), name='repository-search'),
    path("api/docker/info", DockerInfoView.as_view()),
    path('api/profile/', UserProfileDetailView.as_view(), name='profile-detail'),
    path('api/profile/update/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('api/profile/email/', UserEmailUpdateView.as_view(), name='profile-email-update'),
    path('api/profile/password/', UserPasswordChangeView.as_view(), name='profile-password-change'),
    path('api/personal-tokens/', PersonalTokenCreateView.as_view(), name='personal-tokens'),
    path('api/personal-tokens/list/', PersonalTokenListView.as_view(), name='personal-tokens-list'),
]
