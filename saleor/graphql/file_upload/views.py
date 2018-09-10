import json

from django.conf import settings
from graphene_django.views import GraphQLView

# This class is modified verion of the `ModifiedGraphQLView` class from
# `graphene-file-upload` (https://github.com/lmcgartland/graphene-file-upload).


class FileUploadGraphQLView(GraphQLView):
    def dispatch(self, request, *args, **kwargs):
        # Handle options method the GraphQlView restricts it.
        if request.method == 'OPTIONS':
            response = self.options(request, *args, **kwargs)
        else:
            response = super().dispatch(request, *args, **kwargs)
        # Add access control headers
        response['Access-Control-Allow-Origin'] = ','.join(
            settings.ALLOWED_HOSTS)
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response[
            'Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept, Authorization'
        return response

    def dispatch(self, request, *args, **kwargs):
        # Handle options method the GraphQlView restricts it.
        if request.method == 'OPTIONS':
            response =  self.options(request, *args, **kwargs)
        else:
            response = super().dispatch(request, *args, **kwargs)
        # Add access control headers
        response['Access-Control-Allow-Origin'] = ','.join(settings.ALLOWED_HOSTS)
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept, Authorization'
        return response

    @staticmethod
    def get_graphql_params(request, data):
        content_type = GraphQLView.get_content_type(request)

        # Only check multipart/form-data if content_type is not None (this is
        # not checked in the original version from `graphene-file-upload`).
        if content_type and 'multipart/form-data' in content_type:
            query, variables, operation_name, id = super(
                FileUploadGraphQLView, FileUploadGraphQLView).get_graphql_params(
                    request, data)
            operations = data.get('operations')
            files_map = data.get('map')
            try:
                operations = json.loads(operations)
                files_map = json.loads(files_map)
                variables = operations.get('variables')
                for file_key in files_map:
                    # file key is which file it is in the form-data
                    file_instances = files_map[file_key]
                    for file_instance in file_instances:
                        test = obj_set(operations, file_instance, file_key, False)
                query = operations.get('query')
                variables = operations.get('variables')
            except Exception as e:
                raise e
        else:
            query, variables, operation_name, id = super(
                FileUploadGraphQLView, FileUploadGraphQLView).get_graphql_params(
                    request, data)
        return query, variables, operation_name, id


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
        return obj_set(obj, newPath, value, doNotReplace )

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
