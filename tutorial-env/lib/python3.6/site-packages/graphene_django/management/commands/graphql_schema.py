import importlib
import json

from django.core.management.base import BaseCommand, CommandError

from graphene_django.settings import graphene_settings


class CommandArguments(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--schema",
            type=str,
            dest="schema",
            default=graphene_settings.SCHEMA,
            help="Django app containing schema to dump, e.g. myproject.core.schema.schema",
        )

        parser.add_argument(
            "--out",
            type=str,
            dest="out",
            default=graphene_settings.SCHEMA_OUTPUT,
            help="Output file (default: schema.json)",
        )

        parser.add_argument(
            "--indent",
            type=int,
            dest="indent",
            default=graphene_settings.SCHEMA_INDENT,
            help="Output file indent (default: None)",
        )


class Command(CommandArguments):
    help = "Dump Graphene schema JSON to file"
    can_import_settings = True

    def save_file(self, out, schema_dict, indent):
        with open(out, "w") as outfile:
            json.dump(schema_dict, outfile, indent=indent)

    def handle(self, *args, **options):
        options_schema = options.get("schema")

        if options_schema and type(options_schema) is str:
            module_str, schema_name = options_schema.rsplit(".", 1)
            mod = importlib.import_module(module_str)
            schema = getattr(mod, schema_name)

        elif options_schema:
            schema = options_schema

        else:
            schema = graphene_settings.SCHEMA

        out = options.get("out") or graphene_settings.SCHEMA_OUTPUT

        if not schema:
            raise CommandError(
                "Specify schema on GRAPHENE.SCHEMA setting or by using --schema"
            )

        indent = options.get("indent")
        schema_dict = {"data": schema.introspect()}
        self.save_file(out, schema_dict, indent)

        style = getattr(self, "style", None)
        success = getattr(style, "SUCCESS", lambda x: x)

        self.stdout.write(success("Successfully dumped GraphQL schema to %s" % out))
