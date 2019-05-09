import logging
try:
    import simplejson as json
except ImportError:
    import json

from ..exceptions import TransportError, HTTP_EXCEPTIONS

logger = logging.getLogger('elasticsearch')

# create the elasticsearch.trace logger, but only set propagate to False if the
# logger hasn't already been configured
_tracer_already_configured = 'elasticsearch.trace' in logging.Logger.manager.loggerDict
tracer = logging.getLogger('elasticsearch.trace')
if not _tracer_already_configured:
    tracer.propagate = False


class Connection(object):
    """
    Class responsible for maintaining a connection to an Elasticsearch node. It
    holds persistent connection pool to it and it's main interface
    (`perform_request`) is thread-safe.

    Also responsible for logging.
    """
    def __init__(self, host='localhost', port=9200, use_ssl=False, url_prefix='', timeout=10, **kwargs):
        """
        :arg host: hostname of the node (default: localhost)
        :arg port: port to use (integer, default: 9200)
        :arg url_prefix: optional url prefix for elasticsearch
        :arg timeout: default timeout in seconds (float, default: 10)
        """
        scheme = kwargs.get('scheme', 'http')
        if use_ssl or scheme == 'https':
            scheme = 'https'
            use_ssl = True
        self.use_ssl = use_ssl

        self.host = '%s://%s:%s' % (scheme, host, port)
        if url_prefix:
            url_prefix = '/' + url_prefix.strip('/')
        self.url_prefix = url_prefix
        self.timeout = timeout

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.host)

    def _pretty_json(self, data):
        # pretty JSON in tracer curl logs
        try:
            return json.dumps(json.loads(data), sort_keys=True, indent=2, separators=(',', ': ')).replace("'", r'\u0027')
        except (ValueError, TypeError):
            # non-json data or a bulk request
            return data

    def _log_trace(self, method, path, body, status_code, response, duration):
        if not tracer.isEnabledFor(logging.INFO) or not tracer.handlers:
            return

        # include pretty in trace curls
        path = path.replace('?', '?pretty&', 1) if '?' in path else path + '?pretty'
        if self.url_prefix:
            path = path.replace(self.url_prefix, '', 1)
        tracer.info("curl %s-X%s 'http://localhost:9200%s' -d '%s'",
                    "-H 'Content-Type: application/json' " if body else '',
                    method, path, self._pretty_json(body) if body else '')

        if tracer.isEnabledFor(logging.DEBUG):
            tracer.debug('#[%s] (%.3fs)\n#%s', status_code, duration, self._pretty_json(response).replace('\n', '\n#') if response else '')

    def log_request_success(self, method, full_url, path, body, status_code, response, duration):
        """ Log a successful API call.  """
        #  TODO: optionally pass in params instead of full_url and do urlencode only when needed

        # body has already been serialized to utf-8, deserialize it for logging
        # TODO: find a better way to avoid (de)encoding the body back and forth
        if body:
            body = body.decode('utf-8', 'ignore')

        logger.info(
            '%s %s [status:%s request:%.3fs]', method, full_url,
            status_code, duration
        )
        logger.debug('> %s', body)
        logger.debug('< %s', response)

        self._log_trace(method, path, body, status_code, response, duration)

    def log_request_fail(self, method, full_url, path, body, duration, status_code=None, response=None, exception=None):
        """ Log an unsuccessful API call.  """
        # do not log 404s on HEAD requests
        if method == 'HEAD' and status_code == 404:
            return
        logger.warning(
            '%s %s [status:%s request:%.3fs]', method, full_url,
            status_code or 'N/A', duration, exc_info=exception is not None
        )

        # body has already been serialized to utf-8, deserialize it for logging
        # TODO: find a better way to avoid (de)encoding the body back and forth
        if body:
            body = body.decode('utf-8', 'ignore')

        logger.debug('> %s', body)

        self._log_trace(method, path, body, status_code, response, duration)

        if response is not None:
            logger.debug('< %s', response)

    def _raise_error(self, status_code, raw_data):
        """ Locate appropriate exception and raise it. """
        error_message = raw_data
        additional_info = None
        try:
            if raw_data:
                additional_info = json.loads(raw_data)
                error_message = additional_info.get('error', error_message)
                if isinstance(error_message, dict) and 'type' in error_message:
                    error_message = error_message['type']
        except (ValueError, TypeError) as err:
            logger.warning('Undecodable raw error response from server: %s', err)

        raise HTTP_EXCEPTIONS.get(status_code, TransportError)(status_code, error_message, additional_info)


