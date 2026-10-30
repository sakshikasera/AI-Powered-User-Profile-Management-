from pgvector.django import CosineDistance

from profiles.models import Profile
from profiles.serializers import ProfileSerializer


def find_matches(vector, *, limit=10, min_score=0.0, excluded_profile_id=None):
    qs = Profile.objects.select_related("user").filter(
        is_discoverable=True,
        embedding_status=Profile.EmbeddingStatus.READY,
        embedding__isnull=False,
    )
    if excluded_profile_id is not None:
        qs = qs.exclude(pk=excluded_profile_id)
    # ORDER BY cosine distance uses the pgvector vector_cosine_ops HNSW index.
    qs = qs.annotate(distance=CosineDistance("embedding", vector))
    if min_score > 0:
        qs = qs.filter(distance__lte=1.0 - min_score)
    qs = qs.order_by("distance")[:limit]
    return [
        {"profile": ProfileSerializer(p).data,
         "similarity_score": round(max(0.0, min(1.0, 1.0 - float(p.distance))), 4)}
        for p in qs
    ]
