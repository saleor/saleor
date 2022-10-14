"""
This is a script for creating the Google credentials file required
for Google Cloud Storage. This is run during the docker build that
is triggered by a Github action when a PR is merged.
"""


def create_google_credentials_file():
    import json
    import os
    from django.conf import settings

    json_dict = json.loads(settings.GS_JSON)
    file_name = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    with open(file_name, 'w') as f:
        json.dump(json_dict, f)


if __name__ == "django.core.management.commands.shell":
    print('Creating GOOGLE_APPLICATION_CREDENTIALS file')
    create_google_credentials_file()
