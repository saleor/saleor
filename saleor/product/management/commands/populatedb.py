from os.path import exists, join

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from utils.create_random_data import create_items, create_users


class Command(BaseCommand):
    help = 'Populate database with test objects'
    BASE_DIR = r'saleor/static/placeholders/'

    def handle(self, *args, **options):
        for msg in create_items(self.BASE_DIR, 10):
            self.stdout.write(msg)
        for msg in create_users(10):
            self.stdout.write(msg)
