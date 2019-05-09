import json
import logging
import sys
import traceback
import base64
from uuid import UUID

from django.utils.encoding import force_text
try:
    # Django >= 1.10
    from django.urls import resolve, Resolver404
except ImportError:
    # Django < 2.0
    from django.core.urlresolvers import resolve, Resolver404

from silk import models
from silk.collector import DataCollector
from silk.config import SilkyConfig

Logger = logging.getLogger('silk.model_factory')

content_types_json = ['application/json',
                      'application/x-javascript',
                      'text/javascript',
                      'text/x-javascript',
                      'text/x-json']
content_type_form = ['multipart/form-data',
                     'application/x-www-form-urlencoded']
content_type_html = ['text/html']
content_type_css = ['text/css']


class DefaultEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, UUID):
            return str(o)


def _parse_content_type(content_type):
    """best efforts on pulling out the content type and encoding from Content-Type header"""
    try:
        content_type = content_type.strip()
    except AttributeError:
        pass
    char_set = None
    if content_type.strip():
        splt = content_type.split(';')
        content_type = splt[0]
        try:
            raw_char_set = splt[1].strip()
            key, char_set = raw_char_set.split('=')
            if key != 'charset':
                char_set = None
        except (IndexError, ValueError):
            pass
    return content_type, char_set


class RequestModelFactory(object):
    """Produce Request models from Django request objects"""

    def __init__(self, request):
        super(RequestModelFactory, self).__init__()
        self.request = request

    def content_type(self):
        content_type = self.request.META.get('CONTENT_TYPE', '')
        return _parse_content_type(content_type)

    def encoded_headers(self):
        """
        From Django docs (https://docs.djangoproject.com/en/2.0/ref/request-response/#httprequest-objects):

        "With the exception of CONTENT_LENGTH and CONTENT_TYPE, as given above, any HTTP headers in the request are converted to
        META keys by converting all characters to uppercase, replacing any hyphens with underscores and adding an HTTP_ prefix
        to the name. So, for example, a header called X-Bender would be mapped to the META key HTTP_X_BENDER."
        """
        headers = {}
        for k, v in self.request.META.items():
            if k.startswith('HTTP') or k in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                splt = k.split('_')
                if splt[0] == 'HTTP':
                    splt = splt[1:]
                k = '-'.join(splt)
                headers[k] = v
        if SilkyConfig().SILKY_HIDE_COOKIES:
            try:
                del headers['COOKIE']
            except KeyError:
                pass

        return json.dumps(headers, cls=DefaultEncoder)

    def _body(self, raw_body, content_type):
        """
        Encode body as JSON if possible so can be used as a dictionary in generation
        of curl/django test client code
        """
        body = ''
        if content_type in content_type_form:
            body = self.request.POST
            body = json.dumps(dict(body), sort_keys=True, indent=4)
        elif content_type in content_types_json:
            try:
                body = json.dumps(json.loads(raw_body), sort_keys=True, indent=4)
            except:
                body = raw_body
        return body

    def body(self):
        content_type, char_set = self.content_type()
        raw_body = self.request.body
        if char_set:
            try:
                raw_body = raw_body.decode(char_set)
            except AttributeError:
                pass
            except LookupError:  # If no encoding exists, default to UTF-8
                try:
                    raw_body = raw_body.decode('UTF-8')
                except AttributeError:
                    pass
                except UnicodeDecodeError:
                    raw_body = ''
            except Exception as e:
                Logger.error(
                    'Unable to decode request body using char_set %s due to error: %s. Will ignore. Stacktrace:'
                    % (char_set, e)
                )
                traceback.print_exc()
        else:
            # Default to an attempt at UTF-8 decoding.
            try:
                raw_body = raw_body.decode('UTF-8')
            except AttributeError:
                pass
            except UnicodeDecodeError:
                raw_body = ''
        max_size = SilkyConfig().SILKY_MAX_REQUEST_BODY_SIZE
        body = ''
        if raw_body:
            if max_size > -1:
                Logger.debug('A max request size is set so checking size')
                size = sys.getsizeof(raw_body, default=None)
                request_identifier = self.request.path
                if not size:
                    Logger.error(
                        'No way in which to get size of request body for %s, will ignore it',
                        request_identifier
                    )
                elif size <= max_size:
                    Logger.debug(
                        'Request %s has body of size %d which is less than %d so will save the body'
                        % (request_identifier, size, max_size)
                    )
                    body = self._body(raw_body, content_type)
                else:
                    Logger.debug(
                        'Request %s has body of size %d which is greater than %d, therefore ignoring'
                        % (request_identifier, size, max_size)
                    )
                    raw_body = None
            else:
                Logger.debug('No maximum request body size is set, continuing.')
                body = self._body(raw_body, content_type)
        return body, raw_body

    def query_params(self):
        query_params = self.request.GET
        encoded_query_params = ''
        if query_params:
            query_params_dict = dict(zip(query_params.keys(), query_params.values()))
            encoded_query_params = json.dumps(query_params_dict)
        return encoded_query_params

    def view_name(self):
        try:
            resolved = resolve(self.request.path)
        except Resolver404:
            return None

        return resolved.view_name

    def construct_request_model(self):
        body, raw_body = self.body()
        query_params = self.query_params()
        path = self.request.path
        view_name = self.view_name()

        request_model = models.Request.objects.create(
            path=path,
            encoded_headers=self.encoded_headers(),
            method=self.request.method,
            query_params=query_params,
            view_name=view_name,
            body=body)
        # Text fields are encoded as UTF-8 in Django and hence will try to coerce
        # anything to we pass to UTF-8. Some stuff like binary will fail.
        try:
            request_model.raw_body = raw_body
        except UnicodeDecodeError:
            Logger.debug('NYI: Binary request bodies')  # TODO
        Logger.debug('Created new request model with pk %s' % request_model.pk)
        return request_model


class ResponseModelFactory(object):
    """given a response object, craft the silk response model"""

    def __init__(self, response):
        super(ResponseModelFactory, self).__init__()
        self.response = response
        self.request = DataCollector().request

    def body(self):
        body = ''
        content_type, char_set = _parse_content_type(self.response.get('Content-Type', ''))
        content = getattr(self.response, 'content', '')
        if content:
            max_body_size = SilkyConfig().SILKY_MAX_RESPONSE_BODY_SIZE
            if max_body_size > -1:
                Logger.debug('Max size of response body defined so checking')
                size = sys.getsizeof(content, None)
                if not size:
                    Logger.error('Could not get size of response body. Ignoring')
                    content = ''
                else:
                    if size > max_body_size:
                        content = ''
                        Logger.debug(
                            'Size of %d for %s is bigger than %d so ignoring response body'
                            % (size, self.request.path, max_body_size)
                        )
                    else:
                        Logger.debug(
                            'Size of %d for %s is less than %d so saving response body'
                            % (size, self.request.path, max_body_size)
                        )
            if content and content_type in content_types_json:
                # TODO: Perhaps theres a way to format the JSON without parsing it?
                if not isinstance(content, str):
                    # byte string is not compatible with json.loads(...)
                    # and json.dumps(...) in python3
                    content = content.decode()
                try:
                    body = json.dumps(json.loads(content), sort_keys=True, indent=4)
                except (TypeError, ValueError):
                    Logger.warn(
                        'Response to request with pk %s has content type %s but was unable to parse it'
                        % (self.request.pk, content_type)
                    )
        return body, content

    def construct_response_model(self):
        assert self.request, 'Cant construct a response model if there is no request model'
        Logger.debug(
            'Creating response model for request model with pk %s'
            % self.request.pk
        )
        b, content = self.body()
        raw_headers = self.response._headers
        headers = {}
        for k, v in raw_headers.items():
            try:
                header, val = v
            except ValueError:
                header, val = k, v
            finally:
                headers[header] = val
        silky_response = models.Response.objects.create(
            request_id=self.request.id,
            status_code=self.response.status_code,
            encoded_headers=json.dumps(headers),
            body=b
        )

        try:
            silky_response.raw_body = force_text(base64.b64encode(content))
        except TypeError:
            silky_response.raw_body = force_text(base64.b64encode(content.encode('utf-8')))
        return silky_response
