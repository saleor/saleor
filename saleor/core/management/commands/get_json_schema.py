import json
from typing import Type

from django.core.management.base import BaseCommand
from pydantic import BaseModel
from pydantic.schema import schema

from ....app.manifest_schema import Manifest
from ...taxes import TaxData

SCHEMAS: list[Type[BaseModel]] = [Manifest, TaxData]


class Command(BaseCommand):
    help = "Writes selected JSON-schema to stdout"

    def handle(self, *args, **kwargs):
        top_level_schema = schema(SCHEMAS, title="Saleor JSON-schema")
        self.stdout.write(json.dumps(top_level_schema, indent=2))
