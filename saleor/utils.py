import os
import json
import urllib
import contextlib

def fetch_credentials(domain=None):
    try:
        api = os.environ.get('DOMAIN_DATABASE_HOST')
        url = f"{api}/{domain}/database"

        with contextlib.closing(urllib.request.urlopen(url)) as response:
            credentials = response.read().decode('utf-8')
            return json.loads(credentials)
    except Exception as e:
        raise e
