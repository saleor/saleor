from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from social_django.models import Code, Partial


class Command(BaseCommand):
    help = 'removes old not used verification codes and partials'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--age',
            action='store',
            type=int,
            dest='age',
            default=14,
            help='how long to keep unused data (in days, defaults to 14)'
        )

    def handle(self, *args, **options):
        age = timezone.now() - timedelta(days=options['age'])

        # Delete old not verified codes
        Code.objects.filter(
            verified=False,
            timestamp__lt=age
        ).delete()

        # Delete old partial data
        Partial.objects.filter(
            timestamp__lt=age
        ).delete()
