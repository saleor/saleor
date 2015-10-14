from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
WOMBAT_USERNAME = getattr(settings, 'WOMBAT_USERNAME', 'wombat')


class Command(BaseCommand):

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email=WOMBAT_USERNAME, is_active=True)
        if created:
            print('User %s was created' % (WOMBAT_USERNAME,))
        else:
            print('User %s already exists' % (WOMBAT_USERNAME,))

