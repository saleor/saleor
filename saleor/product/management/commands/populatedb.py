from os.path import exists

from django.core.management.base import BaseCommand, CommandError

from utils.create_random_data import create_items, create_users

from saleor.userprofile.models import User


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

    def handle(self, *args, **options):
        for msg in create_items(self.placeholders_dir, 10):
            self.stdout.write(msg)
        for msg in create_users(10):
            self.stdout.write(msg)

        if options['createsuperuser']:
            user = User.objects.create_superuser(
                email='admin@example.com', password='admin')
            self.stdout.write('Superuser - %s' % user.email)
