from django.conf import settings
from django.db import models


class Session(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="caption_sessions")
    title = models.CharField(max_length=255)
    language = models.CharField(max_length=32, default="en")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class TranscriptSegment(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="segments")
    text = models.TextField()
    timestamp = models.FloatField(help_text="Offset in seconds from the start of the session.")
    speaker_label = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["timestamp", "id"]


class Summary(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="summaries")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class UserPreference(models.Model):
    class SummaryStyle(models.TextChoices):
        CONCISE = "concise", "Concise"
        DETAILED = "detailed", "Detailed"
        BULLETS = "bullets", "Bullet points"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences")
    font_size = models.PositiveSmallIntegerField(default=16)
    summary_style = models.CharField(max_length=20, choices=SummaryStyle.choices, default=SummaryStyle.CONCISE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SocialIdentity(models.Model):
    class Provider(models.TextChoices):
        GOOGLE = "google", "Google"
        APPLE = "apple", "Apple"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="social_identities")
    provider = models.CharField(max_length=16, choices=Provider.choices)
    provider_subject = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("provider", "provider_subject"), name="unique_social_provider_subject")
        ]

    def __str__(self):
        return f"{self.provider}:{self.provider_subject}"
