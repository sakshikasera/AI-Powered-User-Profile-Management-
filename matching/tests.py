from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from profiles.models import Profile

User = get_user_model()


def vector(x, y):
    return [float(x), float(y)] + [0.0] * 382


class SemanticMatchingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="searcher", password="SuperPassword987!")
        self.dev_user = User.objects.create_user(username="dev", password="SuperPassword987!")
        self.artist_user = User.objects.create_user(username="artist", password="SuperPassword987!")
        self.private_user = User.objects.create_user(username="private", password="SuperPassword987!")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.source = Profile.objects.create(
            user=self.user, full_name="Searcher", is_discoverable=False,
            embedding=vector(1, 0), embedding_status="ready",
        )
        self.dev = Profile.objects.create(
            user=self.dev_user, full_name="Python Developer", is_discoverable=True,
            embedding=vector(1, 0), embedding_status="ready",
        )
        self.artist = Profile.objects.create(
            user=self.artist_user, full_name="Artist", is_discoverable=True,
            embedding=vector(0, 1), embedding_status="ready",
        )
        self.hidden = Profile.objects.create(
            user=self.private_user, full_name="Hidden Developer", is_discoverable=False,
            embedding=vector(1, 0), embedding_status="ready",
        )

    @patch("matching.views.embed_text", return_value=vector(1, 0))
    def test_text_search_returns_ranked_public_profiles(self, embed):
        response = self.client.post("/api/matching/search/", {"query": "Python backend engineer", "limit": 3, "min_score": 0.5}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["matches"][0]["profile"]["id"], self.dev.pk)
        self.assertGreaterEqual(response.data["matches"][0]["similarity_score"], 0.99)
        self.assertNotIn("embedding", response.data["matches"][0]["profile"])

    def test_profile_similarity_excludes_source_and_private_profiles(self):
        response = self.client.get(f"/api/matching/profiles/{self.source.pk}/similar/?limit=3&min_score=0.5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m["profile"]["id"] for m in response.data["matches"]], [self.dev.pk])
        self.assertEqual(self.client.get(f"/api/matching/profiles/{self.hidden.pk}/similar/").status_code, 404)

    def test_search_validation_and_auth(self):
        self.assertEqual(self.client.post("/api/matching/search/", {"query": "x"}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/matching/search/", {"query": "Python", "limit": 100}, format="json").status_code, 400)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post("/api/matching/search/", {"query": "Python"}, format="json").status_code, 401)
