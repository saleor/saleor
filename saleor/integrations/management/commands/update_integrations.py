from __future__ import unicode_literals

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Updates integration feeds'

    def handle(self, *args, **options):
        pass
