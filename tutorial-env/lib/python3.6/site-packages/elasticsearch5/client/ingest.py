from .utils import NamespacedClient, query_params, _make_path, SKIP_IN_PATH

class IngestClient(NamespacedClient):
    @query_params('master_timeout')
    def get_pipeline(self, id=None, params=None):
        """
        `<https://www.elastic.co/guide/en/elasticsearch/plugins/current/ingest.html>`_

        :arg id: Comma separated list of pipeline ids. Wildcards supported
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        """
        return self.transport.perform_request('GET', _make_path('_ingest',
            'pipeline', id), params=params)

    @query_params('master_timeout', 'timeout')
    def put_pipeline(self, id, body, params=None):
        """
        `<https://www.elastic.co/guide/en/elasticsearch/plugins/current/ingest.html>`_

        :arg id: Pipeline ID
        :arg body: The ingest definition
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg timeout: Explicit operation timeout
        """
        for param in (id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path('_ingest',
            'pipeline', id), params=params, body=body)

    @query_params('master_timeout', 'timeout')
    def delete_pipeline(self, id, params=None):
        """
        `<https://www.elastic.co/guide/en/elasticsearch/plugins/current/ingest.html>`_

        :arg id: Pipeline ID
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg timeout: Explicit operation timeout
        """
        if id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'id'.")
        return self.transport.perform_request('DELETE', _make_path('_ingest',
            'pipeline', id), params=params)

    @query_params('verbose')
    def simulate(self, body, id=None, params=None):
        """
        `<https://www.elastic.co/guide/en/elasticsearch/plugins/current/ingest.html>`_

        :arg body: The simulate definition
        :arg id: Pipeline ID
        :arg verbose: Verbose mode. Display data output for each processor in
            executed pipeline, default False
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('GET', _make_path('_ingest',
            'pipeline', id, '_simulate'), params=params, body=body)
