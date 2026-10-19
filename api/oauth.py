"""Verification of provider tokens and conversion to local application users."""
from dataclasses import dataclass
from hashlib import sha256
import os

from django.contrib.auth import get_user_model
from google.auth.transport.requests import Request
from google.auth.exceptions import GoogleAuthError
from google.oauth2 import id_token as google_id_token
import jwt
from rest_framework_simplejwt.tokens import RefreshToken

from .models import SocialIdentity


class OAuthConfigurationError(Exception):
    pass


class OAuthTokenError(Exception):
    pass


@dataclass(frozen=True)
class VerifiedIdentity:
    subject: str
    email: str = ""


class GoogleTokenVerifier:
    def verify(self, token):
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        if not client_id:
            raise OAuthConfigurationError("Google sign-in is not configured: GOOGLE_OAUTH_CLIENT_ID is missing.")
        try:
            claims = google_id_token.verify_oauth2_token(token, Request(), client_id)
            return VerifiedIdentity(subject=claims["sub"], email=claims.get("email", ""))
        except (GoogleAuthError, ValueError, KeyError) as exc:
            raise OAuthTokenError("The Google identity token is invalid or expired.") from exc


class AppleTokenVerifier:
    issuer = "https://appleid.apple.com"
    jwks_url = "https://appleid.apple.com/auth/keys"

    def verify(self, token):
        client_id = os.environ.get("APPLE_CLIENT_ID")
        if not client_id:
            raise OAuthConfigurationError("Apple sign-in is not configured: APPLE_CLIENT_ID is missing.")
        try:
            signing_key = jwt.PyJWKClient(self.jwks_url).get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=client_id,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
            return VerifiedIdentity(subject=claims["sub"], email=claims.get("email", ""))
        except (jwt.PyJWTError, KeyError, ValueError) as exc:
            raise OAuthTokenError("The Apple identity token is invalid or expired.") from exc


def issue_tokens_for_identity(provider, identity):
    social_identity = SocialIdentity.objects.select_related("user").filter(
        provider=provider, provider_subject=identity.subject
    ).first()
    if social_identity:
        user = social_identity.user
    else:
        user_model = get_user_model()
        username_digest = sha256(f"{provider}:{identity.subject}".encode()).hexdigest()[:24]
        user = user_model.objects.create_user(
            username=f"{provider}_{username_digest}", email=identity.email, password=None
        )
        SocialIdentity.objects.create(
            user=user, provider=provider, provider_subject=identity.subject, email=identity.email
        )
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh), "user": {"id": user.id, "email": user.email}}
