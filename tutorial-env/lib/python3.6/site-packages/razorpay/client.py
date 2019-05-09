import os
import json
import requests
import pkg_resources

from pkg_resources import DistributionNotFound

from types import ModuleType
from .constants import HTTP_STATUS_CODE, ERROR_CODE, URL

from . import resources, utility

from .errors import (BadRequestError, GatewayError,
                     ServerError)


def capitalize_camel_case(string):
    return "".join(map(str.capitalize, string.split('_')))


# Create a dict of resource classes
RESOURCE_CLASSES = {}
for name, module in resources.__dict__.items():
    if isinstance(module, ModuleType) and \
            capitalize_camel_case(name) in module.__dict__:
        RESOURCE_CLASSES[name] = module.__dict__[capitalize_camel_case(name)]

UTILITY_CLASSES = {}
for name, module in utility.__dict__.items():
    if isinstance(module, ModuleType) and name.capitalize() in module.__dict__:
        UTILITY_CLASSES[name] = module.__dict__[name.capitalize()]


class Client:
    """Razorpay client class"""

    DEFAULTS = {
        'base_url': URL.BASE_URL
    }

    def __init__(self, session=None, auth=None, **options):
        """
        Initialize a Client object with session,
        optional auth handler, and options
        """
        self.session = session or requests.Session()
        self.auth = auth
        file_dir = os.path.dirname(__file__)
        self.cert_path = file_dir + '/ca-bundle.crt'

        self.base_url = self._set_base_url(**options)

        self.app_details = []

        # intializes each resource
        # injecting this client object into the constructor
        for name, Klass in RESOURCE_CLASSES.items():
            setattr(self, name, Klass(self))

        for name, Klass in UTILITY_CLASSES.items():
            setattr(self, name, Klass(self))

    def _set_base_url(self, **options):
        base_url = self.DEFAULTS['base_url']

        if 'base_url' in options:
            base_url = options['base_url']
            del(options['base_url'])

        return base_url

    def _update_user_agent_header(self, options):
        user_agent = "{}{} {}".format('Razorpay-Python/', self._get_version(),
                                      self._get_app_details_ua())

        if 'headers' in options:
            options['headers']['User-Agent'] = user_agent
        else:
            options['headers'] = {'User-Agent': user_agent}

        return options

    def _get_version(self):
        version = ""
        try:
            version = pkg_resources.require("razorpay")[0].version
        except DistributionNotFound:  # pragma: no cover
            pass
        return version

    def _get_app_details_ua(self):
        app_details_ua = ""

        app_details = self.get_app_details()

        for app in app_details:
            if 'title' in app:
                app_ua = app['title']
                if 'version' in app:
                    app_ua += "/{}".format(app['version'])
                app_details_ua += "{} ".format(app_ua)

        return app_details_ua

    def set_app_details(self, app_details):
        self.app_details.append(app_details)

    def get_app_details(self):
        return self.app_details

    def request(self, method, path, **options):
        """
        Dispatches a request to the Razorpay HTTP API
        """
        options = self._update_user_agent_header(options)

        url = "{}{}".format(self.base_url, path)

        response = getattr(self.session, method)(url, auth=self.auth,
                                                 verify=self.cert_path,
                                                 **options)
        if ((response.status_code >= HTTP_STATUS_CODE.OK) and
                (response.status_code < HTTP_STATUS_CODE.REDIRECT)):
            return response.json()
        else:
            msg = ""
            code = ""
            json_response = response.json()
            if 'error' in json_response:
                if 'description' in json_response['error']:
                    msg = json_response['error']['description']
                if 'code' in json_response['error']:
                    code = str(json_response['error']['code'])

            if str.upper(code) == ERROR_CODE.BAD_REQUEST_ERROR:
                raise BadRequestError(msg)
            elif str.upper(code) == ERROR_CODE.GATEWAY_ERROR:
                raise GatewayError(msg)
            elif str.upper(code) == ERROR_CODE.SERVER_ERROR:
                raise ServerError(msg)
            else:
                raise ServerError(msg)

    def get(self, path, params, **options):
        """
        Parses GET request options and dispatches a request
        """
        return self.request('get', path, params=params, **options)

    def post(self, path, data, **options):
        """
        Parses POST request options and dispatches a request
        """
        data, options = self._update_request(data, options)
        return self.request('post', path, data=data, **options)

    def patch(self, path, data, **options):
        """
        Parses PATCH request options and dispatches a request
        """
        data, options = self._update_request(data, options)
        return self.request('patch', path, data=data, **options)

    def delete(self, path, data, **options):
        """
        Parses DELETE request options and dispatches a request
        """
        data, options = self._update_request(data, options)
        return self.request('delete', path, data=data, **options)

    def put(self, path, data, **options):
        """
        Parses PUT request options and dispatches a request
        """
        data, options = self._update_request(data, options)
        return self.request('put', path, data=data, **options)

    def _update_request(self, data, options):
        """
        Updates The resource data and header options
        """
        data = json.dumps(data)

        if 'headers' not in options:
            options['headers'] = {}

        options['headers'].update({'Content-type': 'application/json'})

        return data, options
