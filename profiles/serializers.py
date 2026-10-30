from rest_framework import serializers
from .models import Profile


EMBEDDING_SOURCE_FIELDS = frozenset({
    "full_name", "headline", "bio", "occupation", "education", "location",
    "skills", "interests", "experience_years",
})


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    skills = serializers.ListField(
        child=serializers.CharField(max_length=80, allow_blank=False),
        max_length=30, required=False,
    )
    interests = serializers.ListField(
        child=serializers.CharField(max_length=80, allow_blank=False),
        max_length=30, required=False,
    )

    class Meta:
        model = Profile
        fields = (
            "id", "username", "full_name", "headline", "bio", "occupation",
            "education", "location", "skills", "interests", "experience_years",
            "is_discoverable", "ai_summary", "summary_updated_at",
            "embedding_status", "embedding_model", "embedding_updated_at",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "username", "ai_summary", "summary_updated_at", "embedding_status",
            "embedding_model", "embedding_updated_at", "created_at", "updated_at",
        )

    def validate_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Full name cannot be blank.")
        return value

    def validate_experience_years(self, value):
        if value > 80:
            raise serializers.ValidationError("Experience must be at most 80 years.")
        return value

    def validate(self, attrs):
        for field in ("skills", "interests"):
            if field in attrs:
                items = [item.strip() for item in attrs[field]]
                if len({item.casefold() for item in items}) != len(items) or any(not i for i in items):
                    raise serializers.ValidationError({field: "Values must be non-empty and unique."})
                attrs[field] = items
        return attrs

    def update(self, instance, validated_data):
        changed = any(
            name in validated_data and getattr(instance, name) != value
            for name, value in validated_data.items()
            if name in EMBEDDING_SOURCE_FIELDS
        )
        if changed:
            # Never serve stale summaries or embeddings after source data changes.
            instance.ai_summary = ""
            instance.summary_updated_at = None
            instance.embedding = None
            instance.embedding_status = Profile.EmbeddingStatus.PENDING
            instance.embedding_model = ""
            instance.embedding_updated_at = None
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        self.embedding_needs_refresh = changed
        return instance
