from django.core.management.base import BaseCommand
from django.db.models import Q
from django.template.defaultfilters import pluralize

from ...utils import get_refresh_token_model


class Command(BaseCommand):
    help = 'Clears refresh tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--expired',
            action='store_true',
            help='Clears expired tokens',
        )

    def handle(self, expired, *args, **options):
        qs = get_refresh_token_model().objects
        query = Q(revoked__isnull=False)

        if expired:
            qs = qs.expired()
            query |= Q(expired=True)

        deleted, _ = qs.filter(query).delete()

        msg = 'Successfully deleted {} token{}'.format(
            deleted,
            pluralize(deleted))

        self.stdout.write(self.style.SUCCESS(msg))
