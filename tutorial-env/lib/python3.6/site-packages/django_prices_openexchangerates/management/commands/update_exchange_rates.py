from django.core.management.base import BaseCommand

from ...tasks import update_conversion_rates, create_conversion_dates


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all_currencies',
            default=False,
            help='Create entries for all currencies')

    def handle(self, *args, **options):
        if options['all_currencies']:
            all_rates = create_conversion_dates()
        else:
            all_rates = update_conversion_rates()
        for conversion_rate in all_rates:
            self.stdout.write('%s' % (conversion_rate, ))
