from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Profile
from .serializers import ProfileSerializer
from .services import AIServiceError, generate_ai_summary, refresh_profile_embedding


def try_refresh_embedding(profile):
    try:
        refresh_profile_embedding(profile)
    except AIServiceError:
        # The write succeeded. Status 'failed' is returned and may be retried.
        pass


class ProfileListCreateView(generics.ListCreateAPIView):
    serializer_class = ProfileSerializer

    def get_queryset(self):
        return Profile.objects.select_related("user").filter(
            Q(is_discoverable=True) | Q(user=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        if Profile.objects.filter(user=self.request.user).exists():
            raise ValidationError({"detail": "You already have a profile; update /api/profiles/me/ instead."})
        profile = serializer.save(user=self.request.user)
        try_refresh_embedding(profile)


class MyProfileView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return get_object_or_404(Profile.objects.select_related("user"), user=self.request.user)

    def perform_update(self, serializer):
        profile = serializer.save()
        if serializer.embedding_needs_refresh:
            try_refresh_embedding(profile)


class ProfileDetailView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer

    def get_queryset(self):
        return Profile.objects.select_related("user").filter(
            Q(is_discoverable=True) | Q(user=self.request.user)
        )


class SummaryView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "summary"

    def post(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        try:
            summary = generate_ai_summary(profile)
        except AIServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        profile.ai_summary = summary
        profile.summary_updated_at = timezone.now()
        profile.embedding = None
        profile.embedding_status = Profile.EmbeddingStatus.PENDING
        profile.embedding_model = ""
        profile.embedding_updated_at = None
        profile.save()
        try_refresh_embedding(profile)
        return Response(ProfileSerializer(profile).data)


class RefreshEmbeddingView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "search"

    def post(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        try:
            refresh_profile_embedding(profile)
        except AIServiceError as exc:
            return Response({"detail": str(exc), "embedding_status": "failed"}, status=503)
        return Response({
            "id": profile.pk,
            "embedding_status": profile.embedding_status,
            "embedding_model": profile.embedding_model,
            "embedding_updated_at": profile.embedding_updated_at,
        })
