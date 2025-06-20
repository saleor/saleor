import json
import os
import shutil
from typing import cast

from django.core.management.base import BaseCommand
from pydantic import BaseModel

from ....webhook.response_schemas import COMBINED_SCHEMAS_TO_EXPORT, SCHEMAS_TO_EXPORT

SCHEMA_OUTPUT_DIR = "saleor/json_schemas"


class Command(BaseCommand):
    help = "Generate JSON schemas for synchronous webhooks responses."

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
            schema["title"] = self.get_schema_title(schema_cls)
            self.write_schema_to_file(schema, title)

    def export_combined_schemas(self):
        for combined_schema in COMBINED_SCHEMAS_TO_EXPORT:
            title, schemas_cls = combined_schema["title"], combined_schema["schemas"]
            title = cast(str, title)
            defs: dict[str, dict] = {}
            schemas = self.get_schemas(schemas_cls, defs)
            combined_schema_dict = {
                "title": title,
                "anyOf": schemas,
            }
            if defs:
                combined_schema_dict["$defs"] = defs
            self.write_schema_to_file(combined_schema_dict, title)

    def get_schemas(self, schemas_cls, merged_defs):
        schemas = []
        for cls in schemas_cls:
            schema = cls.model_json_schema()

            # move $defs to the top level
            defs = schema.pop("$defs", {})
            merged_defs.update(defs)

            schema["title"] = self.get_schema_title(cls)
            schemas.append(schema)
        return schemas

    @staticmethod
    def get_schema_title(schema_cls: type[BaseModel]) -> str:
        """Get rid of `Schema` suffix from title."""
        title = schema_cls.__name__
        if title.endswith("Schema"):
            title = title.removesuffix("Schema")
        return title

    def write_schema_to_file(self, schema: dict, title: str):
        file_name = f"{title}.json"
        path = os.path.join(SCHEMA_OUTPUT_DIR, file_name)
        with open(path, "w") as f:
            json.dump(schema, f, indent=2)
            f.write("\n")
        self.stdout.write(self.style.SUCCESS(f"Generated {path}"))

    @staticmethod
    def clear_dir():
        if os.path.exists(SCHEMA_OUTPUT_DIR):
            shutil.rmtree(SCHEMA_OUTPUT_DIR)
