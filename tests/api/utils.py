import json


def get_multipart_request_body(query, variables, file, file_name):
    """Create request body for multipart GraphQL requests.

    Multipart requests are different than standard GraphQL requests, because
    of additional 'operations' and 'map' keys.
    """
    return {
        'operations': json.dumps({'query': query, 'variables': variables}),
        'map': json.dumps({file_name: ['variables.file']}), file_name: file}
