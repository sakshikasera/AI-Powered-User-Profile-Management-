from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Profile

User = get_user_model()


class ProfileAPITests(TestCase):
    def setUp(self):
        self.alex = User.objects.create_user(username="alex", password="SuperPassword987!")
        self.jamie = User.objects.create_user(username="jamie", password="SuperPassword987!")
        self.client = APIClient()
        self.client.force_authenticate(user=self.alex)
        self.payload = {
            "full_name": "Alex Smith", "headline": "Python backend developer",
            "bio": "Builds Django REST APIs and PostgreSQL services.",
            "skills": ["Python", "Django", "PostgreSQL"], "interests": ["Machine learning"],
            "experience_years": 4, "is_discoverable": False,
        }

    @patch("profiles.views.refresh_profile_embedding")
    def test_create_and_update_own_profile(self, refresh):
        r = self.client.post("/api/profiles/", self.payload, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["username"], "alex")
        self.assertEqual(r.data["embedding_status"], "pending")
        self.assertEqual(self.client.post("/api/profiles/", self.payload, format="json").status_code, 400)
        pk = r.data["id"]
        response = self.client.patch("/api/profiles/me/", {"headline": "Senior Python developer"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["headline"], "Senior Python developer")
        self.assertEqual(refresh.call_count, 2)
        self.client.force_authenticate(user=self.jamie)
        self.assertEqual(self.client.get(f"/api/profiles/{pk}/").status_code, 404)
        self.assertEqual(self.client.get("/api/profiles/").data["count"], 0)
        self.assertEqual(self.client.patch("/api/profiles/me/", {"headline": "Hacked"}, format="json").status_code, 404)
        self.client.force_authenticate(user=self.alex)
        self.assertEqual(self.client.patch("/api/profiles/me/", {"is_discoverable": True}, format="json").status_code, 200)
        self.assertEqual(refresh.call_count, 2)  # Visibility changes should not recompute vectors.
        self.client.force_authenticate(user=self.jamie)
        self.assertEqual(self.client.get(f"/api/profiles/{pk}/").status_code, 200)
        self.assertEqual(self.client.get("/api/profiles/").data["count"], 1)

    @patch("profiles.views.refresh_profile_embedding")
    def test_summary_generation_and_invalidation(self, embed):
        self.client.post("/api/profiles/", self.payload, format="json")
        with patch("profiles.views.generate_ai_summary", return_value="Alex builds Python APIs."):
            response = self.client.post("/api/profiles/me/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ai_summary"], "Alex builds Python APIs.")
        response = self.client.patch("/api/profiles/me/", {"bio": "Builds data platforms."}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ai_summary"], "")
        self.assertIsNone(response.data["summary_updated_at"])

    def test_profile_input_validation_and_delete(self):
        with patch("profiles.views.refresh_profile_embedding"):
            r = self.client.post("/api/profiles/", {**self.payload, "skills": ["Django", "django"]}, format="json")
            self.assertEqual(r.status_code, 400)
            r = self.client.post("/api/profiles/", self.payload, format="json")
            self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client.delete("/api/profiles/me/").status_code, 204)
        self.assertFalse(Profile.objects.filter(user=self.alex).exists())

    @patch("profiles.services.embed_text")
    def test_embedding_failure_marks_profile_failed(self, embed):
        from .services import AIServiceError, refresh_profile_embedding
        profile = Profile.objects.create(user=self.alex, full_name="Alex Smith")
        embed.side_effect = AIServiceError("Provider unavailable")
        with self.assertRaises(AIServiceError):
            refresh_profile_embedding(profile)
        self.assertEqual(Profile.objects.get(pk=profile.pk).embedding_status, "failed")
