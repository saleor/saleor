from django.core.management.base import BaseCommand

from ...api import schema
from ...schema_printer import print_schema


class Command(BaseCommand):
    help = "Writes SDL for GraphQL API schema to stdout"

    def handle(self, *args, **options):
        self.stdout.write(print_schema(schema))
