import json
import os
import shutil
from typing import cast

from django.core.management.base import BaseCommand
from pydantic import BaseModel

from ....webhook.response_schemas import COMBINED_SCHEMAS_TO_EXPORT, SCHEMAS_TO_EXPORT

SCHEMA_OUTPUT_DIR = "saleor/json_schemas"


class Command(BaseCommand):
    help = "Generate JSON schemas for Pydantic response schemas."

    def handle(self, *args, **options):
        self.clear_dir()
        os.makedirs(SCHEMA_OUTPUT_DIR, exist_ok=True)
        self.export_single_schemas()
        self.export_combined_schemas()

    def export_single_schemas(self):
        for schema_data in SCHEMAS_TO_EXPORT:
            title, schema_cls = schema_data["title"], schema_data["schema"]
            title = cast(str, title)
            schema_cls = cast(type[BaseModel], schema_cls)
            schema = schema_cls.model_json_schema()
            self.write_schema_to_file(schema, title)

    def export_combined_schemas(self):
        for combined_schema in COMBINED_SCHEMAS_TO_EXPORT:
            title, schemas_cls = combined_schema["title"], combined_schema["schemas"]
            title = cast(str, title)
            schemas = self.get_schemas_with_titles(schemas_cls)
            combined_schema_dict = {
                "title": title,
                "anyOf": schemas,
            }
            self.write_schema_to_file(combined_schema_dict, title)

    @staticmethod
    def get_schemas_with_titles(schemas_cls):
        schemas = []
        for cls in schemas_cls:
            schema = cls.model_json_schema()
            schema_title = cls.__name__
            if schema_title.endswith("Schema"):
                schema_title = schema_title.removesuffix("Schema")
            schema["title"] = schema_title
            schemas.append(schema)
        return schemas

    def write_schema_to_file(self, schema: dict, title: str):
        file_name = f"{title}.json"
        path = os.path.join(SCHEMA_OUTPUT_DIR, file_name)
        with open(path, "w") as f:
            json.dump(schema, f, indent=2)
        self.stdout.write(self.style.SUCCESS(f"Generated {path}"))

    @staticmethod
    def clear_dir():
        if os.path.exists(SCHEMA_OUTPUT_DIR):
            shutil.rmtree(SCHEMA_OUTPUT_DIR)
