import json

from django.core.management.base import BaseCommand

from ...api import schema
from ...schema_maps import build_sensitive_fields_map


class Command(BaseCommand):
    help = "Writes sensitive fields map for GraphQL API schema to stdout"

    def handle(self, *args, **options):
        sensitive_fields = build_sensitive_fields_map(schema.get_type_map())
        self.stdout.write(json.dumps(sensitive_fields, indent=4, sort_keys=True))
