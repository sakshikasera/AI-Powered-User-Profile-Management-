from unittest.mock import patch
from django.contrib.auth.models import AnonymousUser, User
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from .views import SearchView


class SearchEndpointUnitTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.authenticated = User(pk=7, username="tester")

    @patch("matching.views.find_matches", return_value=[])
    @patch("matching.views.embed_text", return_value=[0.5] * 384)
    def test_search_routes_validated_query_to_embedder_and_matcher(self, embed, search):
        request = self.factory.post("/api/matching/search/", {
            "query": "Python developer", "limit": 3, "min_score": 0.75,
        }, format="json")
        force_authenticate(request, user=self.authenticated)
        response = SearchView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        embed.assert_called_once_with("Python developer")
        search.assert_called_once_with([0.5] * 384, limit=3, min_score=0.75)

    @patch("matching.views.embed_text")
    def test_rejects_bad_query_before_asking_model(self, embed):
        request = self.factory.post("/api/matching/search/", {"query": "x"}, format="json")
        force_authenticate(request, user=self.authenticated)
        response = SearchView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        embed.assert_not_called()

    def test_requires_auth(self):
        request = self.factory.post("/api/matching/search/", {"query": "Python"}, format="json")
        response = SearchView.as_view()(request)
        self.assertEqual(response.status_code, 401)
