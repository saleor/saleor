from elasticsearch.client.utils import NamespacedClient, query_params, _make_path, SKIP_IN_PATH

class LicenseClient(NamespacedClient):
    @query_params()
    def delete(self, params=None):
        """

        `<https://www.elastic.co/guide/en/x-pack/current/license-management.html>`_
        """
        return self.transport.perform_request('DELETE', '/_xpack/license',
            params=params)

    @query_params('local')
    def get(self, params=None):
        """

        `<https://www.elastic.co/guide/en/x-pack/current/license-management.html>`_

        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        """
        return self.transport.perform_request('GET', '/_xpack/license',
            params=params)

    @query_params('acknowledge')
    def post(self, body=None, params=None):
        """

        `<https://www.elastic.co/guide/en/x-pack/current/license-management.html>`_

        :arg body: licenses to be installed
        :arg acknowledge: whether the user has acknowledged acknowledge messages
            (default: false)
        """
        return self.transport.perform_request('PUT', '/_xpack/license',
            params=params, body=body)

