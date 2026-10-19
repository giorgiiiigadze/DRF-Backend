from unittest.mock import patch
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Session, Summary, TranscriptSegment
from .models import SocialIdentity
from .oauth import VerifiedIdentity


class SessionOwnershipTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.session = Session.objects.create(owner=self.owner, title="Private meeting", language="en")

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_list_and_detail_exclude_another_users_session(self):
        self.authenticate(self.other)
        response = self.client.get(reverse("sessions"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        response = self.client.get(reverse("session-detail", args=[self.session.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_add_segment_to_another_users_session(self):
        self.authenticate(self.other)
        response = self.client.post(reverse("session-segments", args=[self.session.id]), {"text": "secret", "timestamp": 2.5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(TranscriptSegment.objects.count(), 0)

    def test_owner_can_complete_a_session(self):
        self.authenticate(self.owner)
        response = self.client.patch(
            reverse("session-detail", args=[self.session.id]), {"status": "completed"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")
        self.assertIsNotNone(response.data["ended_at"])


class SummaryEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="captioner", password="password123")
        self.session = Session.objects.create(owner=self.user, title="Standup", language="en")
        TranscriptSegment.objects.create(session=self.session, text="We shipped the API.", timestamp=0)
        self.client.force_authenticate(user=self.user)

    @patch("api.views.Summarizer.summarize", return_value="The API shipped.")
    def test_summary_is_created_from_owned_transcript(self, summarize):
        response = self.client.post(reverse("session-summary", args=[self.session.id]), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["text"], "The API shipped.")
        self.assertEqual(Summary.objects.filter(session=self.session).count(), 1)
        summarize.assert_called_once()

    def test_missing_api_configuration_returns_clear_error(self):
        with patch.dict("os.environ", {}, clear=True):
            response = self.client.post(reverse("session-summary", args=[self.session.id]), format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("OPENAI_API_KEY is missing", response.data["detail"])


class OAuthLoginTests(APITestCase):
    @patch("api.views.GoogleTokenVerifier.verify", return_value=VerifiedIdentity("google-subject-123", "person@example.com"))
    def test_google_identity_creates_user_and_returns_application_jwts(self, verify):
        response = self.client.post(reverse("google-oauth-login"), {"id_token": "provider-token"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "person@example.com")
        self.assertTrue(SocialIdentity.objects.filter(provider="google", provider_subject="google-subject-123").exists())

        again = self.client.post(reverse("google-oauth-login"), {"id_token": "provider-token"}, format="json")
        self.assertEqual(again.status_code, status.HTTP_200_OK)
        self.assertEqual(SocialIdentity.objects.filter(provider="google").count(), 1)
        self.assertEqual(verify.call_count, 2)

    def test_google_login_reports_missing_configuration(self):
        with patch.dict("api.oauth.os.environ", {}, clear=True):
            response = self.client.post(reverse("google-oauth-login"), {"id_token": "provider-token"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("GOOGLE_OAUTH_CLIENT_ID is missing", response.data["detail"])
