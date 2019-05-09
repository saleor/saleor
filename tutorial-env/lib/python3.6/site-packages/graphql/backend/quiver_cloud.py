try:
    import requests
except ImportError:
    raise ImportError(
        "requests package is required for Quiver Cloud backend.\n"
        "You can install it using: pip install requests"
    )

from ..utils.schema_printer import print_schema

from .base import GraphQLBackend
from .compiled import GraphQLCompiledDocument

from six.moves.urllib.parse import urlparse

GRAPHQL_QUERY = """
mutation($schemaDsl: String!, $query: String!, $pythonOptions: PythonOptions) {
  generateCode(
    schemaDsl: $schemaDsl
    query: $query,
    language: PYTHON,
    pythonOptions: $pythonOptions
  ) {
    code
    compilationTime
    errors {
      type
    }
  }
}
"""


class GraphQLQuiverCloudBackend(GraphQLBackend):
    def __init__(self, dsn, python_options=None, **options):
        super(GraphQLQuiverCloudBackend, self).__init__(**options)
        try:
            url = urlparse(dsn.strip())
        except Exception:
            raise Exception("Received wrong url {}".format(dsn))

        netloc = url.hostname
        if url.port:
            netloc += ":%s" % url.port

        path_bits = url.path.rsplit("/", 1)
        if len(path_bits) > 1:
            path = path_bits[0]
        else:
            path = ""

        self.api_url = "{}://{}{}".format(url.scheme.rsplit("+", 1)[-1], netloc, path)
        self.public_key = url.username
        self.secret_key = url.password
        self.extra_namespace = {}
        if python_options is None:
            python_options = {"asyncFramework": "PROMISE"}
        wait_for_promises = python_options.pop("wait_for_promises", None)
        if wait_for_promises:
            assert callable(wait_for_promises), "wait_for_promises must be callable."
            self.extra_namespace["wait_for_promises"] = wait_for_promises
        self.python_options = python_options

    def make_post_request(self, url, auth, json_payload):
        """This function executes the request with the provided
        json payload and return the json response"""
        response = requests.post(url, auth=auth, json=json_payload)
        return response.json()

    def generate_source(self, schema, query):
        variables = {
            "schemaDsl": print_schema(schema),
            "query": query,
            "pythonOptions": self.python_options,
        }

        json_response = self.make_post_request(
            "{}/graphql".format(self.api_url),
            auth=(self.public_key, self.secret_key),
            json_payload={"query": GRAPHQL_QUERY, "variables": variables},
        )

        errors = json_response.get("errors")
        if errors:
            raise Exception(errors[0].get("message"))
        data = json_response.get("data", {})
        code_generation = data.get("generateCode", {})
        code = code_generation.get("code")
        if not code:
            raise Exception("Cant get the code. Received json from Quiver Cloud")
        code = str(code)
        return code

    def document_from_string(self, schema, request_string):
        source = self.generate_source(schema, request_string)
        filename = "<document>"
        code = compile(source, filename, "exec")

        def uptodate():
            return True

        document = GraphQLCompiledDocument.from_code(
            schema, code, uptodate, self.extra_namespace
        )
        return document
