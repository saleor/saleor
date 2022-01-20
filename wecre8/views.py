import os

from django.http import HttpResponse


def _send_file(name, attachment_name):
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )
    with open(os.path.join(__location__, name), "r") as f:
        file_data = f.read()

    response = HttpResponse(file_data, content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="{attachment_name}"'
    return response


def apple_aasa(request):
    return _send_file(
        "apple-developer-merchantid-domain-association.txt",
        "apple-app-site-association",
    )
