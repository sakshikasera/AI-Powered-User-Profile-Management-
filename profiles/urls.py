from django.urls import path
from .views import (
    MyProfileView, ProfileDetailView, ProfileListCreateView,
    RefreshEmbeddingView, SummaryView,
)

urlpatterns = [
    path("", ProfileListCreateView.as_view(), name="profile-list-create"),
    path("me/", MyProfileView.as_view(), name="profile-me"),
    path("me/summary/", SummaryView.as_view(), name="profile-generate-summary"),
    path("me/embedding/refresh/", RefreshEmbeddingView.as_view(), name="profile-refresh-embedding"),
    path("<int:pk>/", ProfileDetailView.as_view(), name="profile-detail"),
]
