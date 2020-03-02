from django.core.management.base import BaseCommand
from graphql import print_schema

from ...api import schema


class Command(BaseCommand):
    help = "Writes SDL for GraphQL API schema to stdout"

    def handle(self, *args, **options):
        printed_schema = print_schema(schema)
        schema_lines = printed_schema.splitlines()
        for index, line in enumerate(schema_lines):
            if "implements" in line:
                schema_lines[index] = line.replace(",", " &")
        printed_schema = "\n".join(schema_lines)
        self.stdout.write(printed_schema)
