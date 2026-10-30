from django.urls import path
from .views import SearchView, SimilarProfilesView

urlpatterns = [
    path("search/", SearchView.as_view(), name="semantic-search"),
    path("profiles/<int:pk>/similar/", SimilarProfilesView.as_view(), name="similar-profiles"),
]
