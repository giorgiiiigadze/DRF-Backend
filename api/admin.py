from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Session, Summary, TranscriptSegment, UserPreference


class TranscriptSegmentInline(admin.TabularInline):
    model = TranscriptSegment
    extra = 0


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "language", "status", "created_at", "updated_at", "ended_at")
    list_filter = ("language", "status", "created_at")
    search_fields = ("title", "owner__username")
    inlines = (TranscriptSegmentInline,)


@admin.register(TranscriptSegment)
class TranscriptSegmentAdmin(admin.ModelAdmin):
    list_display = ("session", "timestamp", "speaker_label", "created_at", "updated_at")
    search_fields = ("text", "speaker_label")


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ("session", "created_at", "updated_at")


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "font_size", "summary_style", "updated_at")


# Django's Group model remains in the database for future role-based permissions,
# but this app does not expose group management in its admin UI.
admin.site.unregister(Group)
