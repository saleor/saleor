from os.path import exists, join

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from utils.create_random_data import create_items, create_users


class Command(BaseCommand):
    help = 'Populate database with test objects'
    BASE_DIR = r'saleor/static/placeholders/'
    required_dirs = [join(BASE_DIR, 'shirts'), join(BASE_DIR, 'bags')]

    def handle(self, *args, **options):
        if not all(exists(path) for path in self.required_dirs):
            msg = 'Directories %s with images are required.' % ', '.join(
                self.required_dirs)
            raise CommandError(msg)
        for msg in create_items(self.BASE_DIR, 10):
            self.stdout.write(msg)
        for msg in create_users(10):
            self.stdout.write(msg)
