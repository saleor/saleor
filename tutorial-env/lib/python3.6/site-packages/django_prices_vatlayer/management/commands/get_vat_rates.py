from django.core.management.base import BaseCommand

from ... import utils


class Command(BaseCommand):
    help = 'Get current vat rates in european country and saves to database'

    def handle(self, *args, **options):
        json_response_rates = utils.fetch_vat_rates()
        utils.create_objects_from_json(json_response_rates)

        json_response_types = utils.fetch_rate_types()
        utils.save_vat_rate_types(json_response_types)
