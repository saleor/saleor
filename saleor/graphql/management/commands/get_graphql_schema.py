from django.core.management.base import BaseCommand
from graphql import print_schema

from ...api import schema


class Command(BaseCommand):
    help = 'Writes SDL for GraphQL API schema to stdout'

    def handle(self, *args, **options):
        self.stdout.write(print_schema(schema))
