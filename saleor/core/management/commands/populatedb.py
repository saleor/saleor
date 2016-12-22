from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from ....userprofile.models import User
from ...utils.random_data import (
    create_orders, create_users, create_shipping_methods,
    create_items_by_schema)


class Command(BaseCommand):
    help = 'Populate database with test objects'
    placeholders_dir = r'saleor/static/placeholders/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--createsuperuser',
            action='store_true',
            dest='createsuperuser',
            default=False,
            help='Create admin account')
        parser.add_argument(
            '--withoutimages',
            action='store_true',
            dest='withoutimages',
            default=False,
            help='Don\'t create product images')
        parser.add_argument(
            '--withoutsearch',
            action='store_true',
            dest='withoutsearch',
            default=False,
            help='Don\'t update search index')

    def make_database_faster(self):
        '''Sacrifices some of the safeguards of sqlite3 for speed

        Users are not likely to run this command in a production environment.
        They are even less likely to run it in production while using sqlite3.
        '''
        if 'sqlite3' in connection.settings_dict['ENGINE']:
            cursor = connection.cursor()
            cursor.execute('PRAGMA temp_store = MEMORY;')
            cursor.execute('PRAGMA synchronous = OFF;')

    def populate_search_index(self):
        call_command('update_index')

    def handle(self, *args, **options):
        self.make_database_faster()
        create_images = not options['withoutimages']
        for msg in create_shipping_methods():
            self.stdout.write(msg)
        create_items_by_schema(self.placeholders_dir, 10, create_images,
                               stdout=self.stdout)
        for msg in create_users(20):
            self.stdout.write(msg)
        for msg in create_orders(20):
            self.stdout.write(msg)

        if options['createsuperuser']:
            credentials = {'email': 'admin@example.com', 'password': 'admin'}
            user, created = User.objects.get_or_create(
                email=credentials['email'], defaults={
                    'is_active': True, 'is_staff': True, 'is_superuser': True})
            if created:
                user.set_password(credentials['password'])
                user.save()
                self.stdout.write(
                    'Superuser - %(email)s/%(password)s' % credentials)
            else:
                self.stdout.write(
                    'Superuser already exists - %(email)s' % credentials)
        if not options['withoutsearch']:
            self.populate_search_index()
