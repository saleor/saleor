from elasticsearch.client.utils import NamespacedClient, query_params, _make_path

class DeprecationClient(NamespacedClient):
    @query_params()
    def info(self, index=None, params=None):
        """
        `<http://www.elastic.co/guide/en/migration/current/migration-api-deprecation.html>`_

        :arg index: Index pattern
        """
        return self.transport.perform_request('GET', _make_path(index, '_xpack',
            'migration', 'deprecations'), params=params)

