from django.core.management.base import BaseCommand
from graphql import print_schema

from ...api import schema


class Command(BaseCommand):
    help = "Writes SDL for GraphQL API schema to stdout"

    def handle(self, *args, **options):
        """Support multiple interface notation in schema for Apollo tooling.

        In `graphql-core` V2 separator for interaces is `,`.
        Apollo tooling to generate TypeScript types using `&` as interfaces separator.
        https://github.com/graphql-python/graphql-core/pull/258
        """
        printed_schema = print_schema(schema)
        for line in printed_schema.splitlines():
            if "implements" in line:
                line = line.replace(",", " &")
            self.stdout.write(f"{line}\n")
