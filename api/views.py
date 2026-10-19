from django.db import transaction
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Session, Summary, UserPreference
from .oauth import AppleTokenVerifier, GoogleTokenVerifier, OAuthConfigurationError, OAuthTokenError, issue_tokens_for_identity
from .serializers import AppleOAuthSerializer, GoogleOAuthSerializer, RegisterSerializer, SessionSerializer, SummarySerializer, TranscriptSegmentSerializer, UserPreferenceSerializer
from .services import Summarizer, SummarizerError


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({"id": response.data["id"], "username": response.data["username"], "email": response.data.get("email", "")}, status=status.HTTP_201_CREATED)


class OAuthLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = None
    verifier_class = None
    token_field = None
    provider = None

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            identity = self.verifier_class().verify(serializer.validated_data[self.token_field])
            tokens = issue_tokens_for_identity(self.provider, identity)
        except OAuthConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except OAuthTokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(tokens, status=status.HTTP_200_OK)


class GoogleOAuthLoginView(OAuthLoginView):
    serializer_class = GoogleOAuthSerializer
    verifier_class = GoogleTokenVerifier
    token_field = "id_token"
    provider = "google"


class AppleOAuthLoginView(OAuthLoginView):
    serializer_class = AppleOAuthSerializer
    verifier_class = AppleTokenVerifier
    token_field = "identity_token"
    provider = "apple"


class SessionListCreateView(generics.ListCreateAPIView):
    serializer_class = SessionSerializer

    def get_queryset(self):
        return Session.objects.filter(owner=self.request.user).prefetch_related("segments", "summaries")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SessionDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = SessionSerializer

    def get_queryset(self):
        return Session.objects.filter(owner=self.request.user).prefetch_related("segments", "summaries")


def owned_session(user, session_id):
    try:
        return Session.objects.get(id=session_id, owner=user)
    except Session.DoesNotExist:
        raise NotFound("Session not found.")


class TranscriptSegmentCreateView(APIView):
    def post(self, request, session_id):
        session = owned_session(request.user, session_id)
        serializer = TranscriptSegmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        segment = serializer.save(session=session)
        session.save(update_fields=["updated_at"])
        return Response(TranscriptSegmentSerializer(segment).data, status=status.HTTP_201_CREATED)


class SessionSummaryView(APIView):
    def get(self, request, session_id):
        session = owned_session(request.user, session_id)
        return Response(SummarySerializer(session.summaries.all(), many=True).data)

    def post(self, request, session_id):
        session = owned_session(request.user, session_id)
        preference, _ = UserPreference.objects.get_or_create(user=request.user)
        transcript = "\n".join(
            f"[{segment.timestamp:.2f}s] {segment.speaker_label + ': ' if segment.speaker_label else ''}{segment.text}"
            for segment in session.segments.all()
        )
        try:
            text = Summarizer().summarize(transcript, preference.summary_style)
        except SummarizerError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        with transaction.atomic():
            summary = Summary.objects.create(session=session, text=text)
            session.save(update_fields=["updated_at"])
        return Response(SummarySerializer(summary).data, status=status.HTTP_201_CREATED)


class UserPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = UserPreferenceSerializer

    def get_object(self):
        preference, _ = UserPreference.objects.get_or_create(user=self.request.user)
        return preference
