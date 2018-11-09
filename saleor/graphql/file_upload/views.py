import json

from django.conf import settings
from django.http import HttpRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render_to_response
from django.views.generic import View
from graphene_django.settings import graphene_settings
from graphene_django.views import instantiate_middleware
from graphql import get_default_backend
from graphql.error import GraphQLError, format_error as format_graphql_error
from graphql.execution import ExecutionResult


class FileUploadGraphQLView(View):
    # This class was inspired by the `FileUploadGraphQLView` class from
    # https://github.com/lmcgartland/graphene-file-upload
    schema = None
    executor = None
    backend = None
    middleware = None
    root_value = None

    def __init__(
            self,
            schema=None,
            executor=None,
            middleware=None,
            root_value=None,
            backend=None):
        if schema is None:
            schema = graphene_settings.SCHEMA
        if backend is None:
            backend = get_default_backend()
        if middleware is None:
            middleware = graphene_settings.MIDDLEWARE
        self.schema = self.schema or schema
        if middleware is not None:
            self.middleware = list(instantiate_middleware(middleware))
        self.executor = executor
        self.root_value = root_value
        self.backend = backend

    def dispatch(self, request, *args, **kwargs):
        # Handle options method the GraphQlView restricts it.
        if request.method == 'GET':
            return render_to_response('graphql/playground.html')
        if request.method == 'OPTIONS':
            response = self.options(request, *args, **kwargs)
        elif request.method == 'POST':
            response = self.handle_query(request, *args, **kwargs)
        else:
            return HttpResponseNotAllowed(
                ['GET', 'OPTIONS', 'POST'])
        # Add access control headers
        response['Access-Control-Allow-Origin'] = (
            settings.ALLOWED_GRAPHQL_ORIGINS)
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = (
            'Origin, Content-Type, Accept, Authorization')
        return response

    def handle_query(self, request: HttpRequest, *args, **kwargs):
        try:
            data = self.parse_body(request)
        except ValueError as e:
            return JsonResponse(
                data={
                    'errors': [self.format_error('Unable to parse query.')]},
                status=400)
        if isinstance(data, list):
            responses = [self.get_response(request, entry) for entry in data]
            result = [response for response, code in responses]
            status_code = max((code for response, code in responses),
                              default=200)
        else:
            result, status_code = self.get_response(request, data)
        return JsonResponse(
            data=result,
            status=status_code)

    def get_response(self, request: HttpRequest, data: dict):
        query, variables, operation_name = self.get_graphql_params(
            request, data)
        execution_result = self.execute_graphql_request(
            request, query, variables, operation_name)
        status_code = 200
        if execution_result:
            response = {}
            if execution_result.errors:
                response['errors'] = [
                    self.format_error(e) for e in execution_result.errors]
            if execution_result.invalid:
                status_code = 400
            else:
                response['data'] = execution_result.data
            result = response
        else:
            result = None
        return result, status_code

    def get_root_value(self, request: HttpRequest):
        return self.root_value

    def execute_graphql_request(
            self, request: HttpRequest, query: str, variables: dict,
            operation_name: str):
        if not query:
            return ExecutionResult(
                errors=[ValueError('Must provide a query string.')],
                invalid=True)
        try:
            document = self.backend.document_from_string(self.schema, query)
        except ValueError as e:
            return ExecutionResult(errors=[e], invalid=True)
        extra_options = {}
        if self.executor:
            # We only include it optionally since
            # executor is not a valid argument in all backends
            extra_options['executor'] = self.executor
        try:
            return document.execute(
                root=self.get_root_value(request),
                variables=variables,
                operation_name=operation_name,
                context=request,
                middleware=self.middleware,
                **extra_options)
        except Exception as e:
            return ExecutionResult(errors=[e], invalid=True)

    @staticmethod
    def parse_body(request: HttpRequest):
        content_type = request.content_type
        if content_type == 'application/graphql':
            return {'query': request.body.decode('utf-8')}
        if content_type == 'application/json':
            body = request.body.decode('utf-8')
            return json.loads(body)
        if content_type in ['application/x-www-form-urlencoded',
                            'multipart/form-data']:
            return request.POST
        return {}

    @staticmethod
    def get_graphql_params(request: HttpRequest, data: dict):
        query = data.get('query')
        variables = data.get('variables')
        operation_name = data.get('operationName')
        if operation_name == 'null':
            operation_name = None
        if request.content_type == 'multipart/form-data':
            operations = json.loads(data.get('operations', '{}'))
            files_map = json.loads(data.get('map', '{}'))
            for file_key in files_map:
                # file key is which file it is in the form-data
                file_instances = files_map[file_key]
                for file_instance in file_instances:
                    test = obj_set(operations, file_instance, file_key, False)
            query = operations.get('query')
            variables = operations.get('variables')
        return query, variables, operation_name

    @staticmethod
    def format_error(error):
        if isinstance(error, GraphQLError):
            return format_graphql_error(error)
        return {'message': str(error)}


def getKey(key):
    try:
        intKey = int(key)
        return intKey
    except:
        return key


def getShallowProperty(obj, prop):
    if type(prop) is int:
        return obj[prop]

    try:
        return obj.get(prop)
    except:
        return None


def obj_set(obj, path, value, doNotReplace):
    if type(path) is int:
        path = [path]
    if path is None or len(path) == 0:
        return obj
    if isinstance(path, str):
        newPath = list(map(getKey, path.split('.')))
        return obj_set(obj, newPath, value, doNotReplace)

    currentPath = path[0]
    currentValue = getShallowProperty(obj, currentPath)

    if len(path) == 1:
        if currentValue is None or not doNotReplace:
            obj[currentPath] = value

    if currentValue is None:
        try:
            if type(path[1]) == int:
                obj[currentPath] = []
            else:
                obj[currentPath] = {}
        except Exception as e:
            pass

    return obj_set(obj[currentPath], path[1:], value, doNotReplace)
