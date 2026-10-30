from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "user", "is_discoverable", "embedding_status", "created_at")
    list_filter = ("is_discoverable", "embedding_status")
    search_fields = ("full_name", "user__username", "headline", "skills")
    readonly_fields = (
        "embedding_status", "embedding_model", "embedding_updated_at",
        "summary_updated_at", "created_at", "updated_at",
    )
    exclude = ("embedding",)
