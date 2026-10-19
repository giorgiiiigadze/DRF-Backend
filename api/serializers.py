from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from .models import Session, Summary, TranscriptSegment, UserPreference


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "username", "password", "email")
        read_only_fields = ("id",)
        extra_kwargs = {"email": {"required": False}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class GoogleOAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True, trim_whitespace=True)


class AppleOAuthSerializer(serializers.Serializer):
    identity_token = serializers.CharField(write_only=True, trim_whitespace=True)


class TranscriptSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptSegment
        fields = ("id", "text", "timestamp", "speaker_label", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_timestamp(self, value):
        if value < 0:
            raise serializers.ValidationError("Timestamp must be zero or greater.")
        return value


class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = ("id", "text", "created_at", "updated_at")
        read_only_fields = fields


class SessionSerializer(serializers.ModelSerializer):
    segments = TranscriptSegmentSerializer(many=True, read_only=True)
    summaries = SummarySerializer(many=True, read_only=True)

    class Meta:
        model = Session
        fields = ("id", "title", "language", "status", "created_at", "updated_at", "ended_at", "segments", "summaries")
        read_only_fields = ("id", "created_at", "updated_at", "segments", "summaries")

    def update(self, instance, validated_data):
        if validated_data.get("status") == Session.Status.COMPLETED and not validated_data.get("ended_at") and not instance.ended_at:
            validated_data["ended_at"] = timezone.now()
        return super().update(instance, validated_data)


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ("font_size", "summary_style", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")

    def validate_font_size(self, value):
        if not 8 <= value <= 72:
            raise serializers.ValidationError("Font size must be between 8 and 72.")
        return value
