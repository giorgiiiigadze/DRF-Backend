from django.contrib import admin
from .models import Session, Summary, TranscriptSegment, UserPreference


class TranscriptSegmentInline(admin.TabularInline):
    model = TranscriptSegment
    extra = 0


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "language", "created_at")
    list_filter = ("language", "created_at")
    search_fields = ("title", "owner__username")
    inlines = (TranscriptSegmentInline,)


@admin.register(TranscriptSegment)
class TranscriptSegmentAdmin(admin.ModelAdmin):
    list_display = ("session", "timestamp", "speaker_label")
    search_fields = ("text", "speaker_label")


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ("session", "created_at")


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "font_size", "summary_style")
