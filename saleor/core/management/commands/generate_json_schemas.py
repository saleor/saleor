import json
import os
from typing import cast

from django.core.management.base import BaseCommand
from pydantic import BaseModel

from ....webhook.response_schemas import SCHEMAS_TO_EXPORT

SCHEMA_OUTPUT_DIR = "saleor/json_schemas"


class Command(BaseCommand):
    help = "Generate JSON schemas for Pydantic response schemas."

    def handle(self, *args, **options):
        os.makedirs(SCHEMA_OUTPUT_DIR, exist_ok=True)

        for schema_cls in SCHEMAS_TO_EXPORT:
            filename = f"{schema_cls.__name__}.json"
            schema_cls = cast(type[BaseModel], schema_cls)
            schema = schema_cls.model_json_schema()
            path = os.path.join(SCHEMA_OUTPUT_DIR, filename)
            with open(path, "w") as f:
                json.dump(schema, f, indent=2)
            self.stdout.write(self.style.SUCCESS(f"Generated {path}"))
