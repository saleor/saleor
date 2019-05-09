from elasticsearch.client.utils import NamespacedClient, query_params, _make_path, SKIP_IN_PATH

class MonitoringClient(NamespacedClient):
    @query_params('interval', 'system_api_version', 'system_id')
    def bulk(self, body, doc_type=None, params=None):
        """
        `<http://www.elastic.co/guide/en/monitoring/current/appendix-api-bulk.html>`_

        :arg body: The operation definition and data (action-data pairs),
            separated by newlines
        :arg doc_type: Default document type for items which don't provide one
        :arg interval: Collection interval (e.g., '10s' or '10000ms') of the
            payload
        :arg system_api_version: API Version of the monitored system
        :arg system_id: Identifier of the monitored system
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('POST', _make_path('_xpack',
            'monitoring', doc_type, '_bulk'), params=params,
            body=self.client._bulk_body(body))
