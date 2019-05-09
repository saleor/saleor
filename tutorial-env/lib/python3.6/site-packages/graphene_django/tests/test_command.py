from django.core import management
from mock import patch
from six import StringIO


@patch("graphene_django.management.commands.graphql_schema.Command.save_file")
def test_generate_file_on_call_graphql_schema(savefile_mock, settings):
    out = StringIO()
    management.call_command("graphql_schema", schema="", stdout=out)
    assert "Successfully dumped GraphQL schema to schema.json" in out.getvalue()
