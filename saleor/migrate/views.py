import dj_database_url
from django.conf import settings
from django.http import HttpResponse
from django.core.management import execute_from_command_line
from ..utils import fetch_credentials

def migrate(request):
    domain = request.headers["X-Domain-ID"]
    credentials = fetch_credentials(domain)

    client = credentials.get('client')
    connection = credentials.get('connection')

    host = connection.get('host')
    port = connection.get('port')
    user = connection.get('user')
    password = connection.get('password')
    database = connection.get('database')

    connection_string = f"{client}://{user}:{password}@{host}:{port}/{database}"
    settings.DATABASES["dynamic-database"] = dj_database_url.parse(connection_string)

    execute_from_command_line([
        '../../manage.py',
        'migrate',
        '--database',
        'dynamic-database'
    ])

    response = HttpResponse(status=204)
    return response
