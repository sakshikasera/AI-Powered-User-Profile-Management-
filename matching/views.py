from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from profiles.models import Profile
from profiles.services import AIServiceError, embed_text
from .serializers import MatchParametersSerializer, SearchSerializer
from .services import find_matches


class SearchView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "search"

    def post(self, request):
        params = SearchSerializer(data=request.data)
        params.is_valid(raise_exception=True)
        query = params.validated_data["query"]
        try:
            vector = embed_text(query)
        except AIServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        matches = find_matches(
            vector,
            limit=params.validated_data["limit"],
            min_score=params.validated_data["min_score"],
        )
        return Response({"query": query, "count": len(matches), "matches": matches})


class SimilarProfilesView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "search"

    def get(self, request, pk):
        params = MatchParametersSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        # The source may be private only when it belongs to the requester.
        source = get_object_or_404(Profile.objects.filter(
            Q(is_discoverable=True) | Q(user=request.user)
        ), pk=pk)
        if source.embedding_status != Profile.EmbeddingStatus.READY or source.embedding is None:
            return Response({"detail": "Source profile embedding is not ready. Refresh it first."}, status=409)
        matches = find_matches(
            source.embedding,
            excluded_profile_id=source.pk,
            limit=params.validated_data["limit"],
            min_score=params.validated_data["min_score"],
        )
        return Response({"source_profile_id": source.pk, "count": len(matches), "matches": matches})
