from os.path import exists

from django.core.management.base import BaseCommand, CommandError

from utils.create_random_data import create_items, create_users


class Command(BaseCommand):
    help = 'Populate database with test objects'
    placeholders_dir = r'saleor/static/placeholders/'

    def handle(self, *args, **options):
        if not exists(self.placeholders_dir):
            msg = 'Directory %s with images is required.' % self.placeholders_dir
            raise CommandError(msg)
        for msg in create_items(self.placeholders_dir, 10):
            self.stdout.write(msg)
        for msg in create_users(10):
            self.stdout.write(msg)
