import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
from django.test import SimpleTestCase, override_settings
from .models import Profile
from .services import AIServiceError, embed_text, generate_ai_summary, profile_source_text


class ProfileServiceUnitTests(SimpleTestCase):
    def test_profile_source_text(self):
        profile = Profile(full_name="Alex Smith", headline="Backend developer", skills=["Python", "Django"], interests=[])
        text = profile_source_text(profile)
        self.assertIn("Skills: Python, Django", text)
        self.assertIn("Headline: Backend developer", text)

    @override_settings(OPENAI_API_KEY="test-key")
    def test_ai_summary_calls_responses_api(self):
        client_class = Mock()
        client_class.return_value.responses.create.return_value = SimpleNamespace(output_text="An experienced Python developer.")
        with patch.dict(sys.modules, {"openai": SimpleNamespace(OpenAI=client_class)}):
            summary = generate_ai_summary(Profile(full_name="Alex Smith", skills=["Python"], interests=[]))
        self.assertEqual(summary, "An experienced Python developer.")
        kwargs = client_class.return_value.responses.create.call_args.kwargs
        self.assertIs(kwargs["store"], False)
        self.assertIn("Alex Smith", kwargs["input"])

    @override_settings(OPENAI_API_KEY="")
    def test_requires_api_key_for_real_summary(self):
        with self.assertRaises(AIServiceError):
            generate_ai_summary(Profile(full_name="Alex Smith", skills=[], interests=[]))

    @patch("profiles.services.get_embedding_model")
    def test_vector_shape_validation(self, getter):
        getter.return_value.encode.return_value = SimpleNamespace(tolist=lambda: [1.0] * 384)
        self.assertEqual(len(embed_text("Python")), 384)
        getter.return_value.encode.return_value = SimpleNamespace(tolist=lambda: [1.0] * 768)
        with self.assertRaises(AIServiceError):
            embed_text("Python")
