from django.core.management.base import BaseCommand

from ....wishlist.utils import update_and_send_wishlist_notifications


class Command(BaseCommand):
    help = 'Update and send wishlist notifications'

    def handle(self, *args, **options):
        update_and_send_wishlist_notifications()
