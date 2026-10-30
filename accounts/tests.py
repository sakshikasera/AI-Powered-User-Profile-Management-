from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_registration_login_me_refresh_and_logout(self):
        response = self.client.post("/api/auth/register/", {
            "username": "alex", "email": "alex@example.com",
            "password": "A-Very-Strong-Test-Password-9821", "password_confirm": "A-Very-Strong-Test-Password-9821",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data)
        self.assertNotIn("password", response.data["user"])
        self.assertTrue(User.objects.get(username="alex").check_password("A-Very-Strong-Test-Password-9821"))
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["access"])
        self.assertEqual(self.client.get("/api/auth/me/").data["username"], "alex")
        refresh = response.data["refresh"]
        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json").status_code, 205)
        self.assertEqual(self.client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json").status_code, 401)

    def test_registration_validation(self):
        payload = {
            "username": "alex", "email": "alex@example.com",
            "password": "A-Very-Strong-Test-Password-9821", "password_confirm": "no-match",
        }
        self.assertEqual(self.client.post("/api/auth/register/", payload, format="json").status_code, 400)
        payload["password_confirm"] = payload["password"]
        self.assertEqual(self.client.post("/api/auth/register/", payload, format="json").status_code, 201)
        payload["username"] = "alex2"
        payload["email"] = "ALEX@example.com"
        self.assertEqual(self.client.post("/api/auth/register/", payload, format="json").status_code, 400)

    def test_private_auth_endpoint_requires_token(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_logout_cannot_blacklist_another_users_token(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        owner = User.objects.create_user(username="owner", password="SuperPassword987!", email="owner@example.com")
        someone_else = User.objects.create_user(username="other", password="SuperPassword987!", email="other@example.com")
        foreign_refresh = str(RefreshToken.for_user(owner))
        self.client.force_authenticate(user=someone_else)
        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": foreign_refresh}, format="json").status_code, 400)
