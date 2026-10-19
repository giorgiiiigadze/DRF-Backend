from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import AppleOAuthLoginView, GoogleOAuthLoginView, RegisterView, SessionDetailView, SessionListCreateView, SessionSummaryView, TranscriptSegmentCreateView, UserPreferenceView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/google/", GoogleOAuthLoginView.as_view(), name="google-oauth-login"),
    path("auth/apple/", AppleOAuthLoginView.as_view(), name="apple-oauth-login"),
    path("sessions/", SessionListCreateView.as_view(), name="sessions"),
    path("sessions/<int:pk>/", SessionDetailView.as_view(), name="session-detail"),
    path("sessions/<int:session_id>/segments/", TranscriptSegmentCreateView.as_view(), name="session-segments"),
    path("sessions/<int:session_id>/summary/", SessionSummaryView.as_view(), name="session-summary"),
    path("preferences/", UserPreferenceView.as_view(), name="preferences"),
]
