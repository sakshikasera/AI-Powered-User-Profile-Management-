from django.core.management.base import BaseCommand
from profiles.models import Profile
from profiles.services import AIServiceError, refresh_profile_embedding


class Command(BaseCommand):
    help = "Recompute all profile embeddings (e.g. after changing the model)"

    def add_arguments(self, parser):
        parser.add_argument("--only-failed", action="store_true", help="Rebuild only failed/pending profiles")

    def handle(self, *args, **options):
        qs = Profile.objects.order_by("pk")
        if options["only_failed"]:
            qs = qs.exclude(embedding_status=Profile.EmbeddingStatus.READY)
        ok = failed = 0
        for profile in qs.iterator():
            try:
                refresh_profile_embedding(profile)
                ok += 1
            except AIServiceError as exc:
                failed += 1
                self.stderr.write(f"Profile {profile.pk}: {exc}")
        self.stdout.write(self.style.SUCCESS(f"Indexed {ok}; failed {failed}."))
