from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField


class Profile(models.Model):
    class EmbeddingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=150)
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True, max_length=3000)
    occupation = models.CharField(max_length=150, blank=True)
    education = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=150, blank=True)
    skills = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    is_discoverable = models.BooleanField(default=False)

    ai_summary = models.TextField(blank=True)
    summary_updated_at = models.DateTimeField(null=True, blank=True)
    embedding = VectorField(dimensions=384, null=True, blank=True)
    embedding_status = models.CharField(
        max_length=10, choices=EmbeddingStatus.choices, default=EmbeddingStatus.PENDING
    )
    embedding_model = models.CharField(max_length=160, blank=True)
    embedding_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["is_discoverable", "embedding_status"], name="profiles_public_ready_idx"),
            HnswIndex(
                name="profiles_embed_hnsw_idx", fields=["embedding"],
                m=16, ef_construction=64, opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"
