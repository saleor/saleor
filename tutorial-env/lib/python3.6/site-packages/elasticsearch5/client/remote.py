from .utils import NamespacedClient, query_params, _make_path, SKIP_IN_PATH

class RemoteClient(NamespacedClient):
    @query_params()
    def info(self, params=None):
        """
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-remote-info.html>`_
        """
        return self.transport.perform_request('GET', '/_remote/info',
            params=params)

