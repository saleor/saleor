from .utils import NamespacedClient, query_params, _make_path, SKIP_IN_PATH

class SnapshotClient(NamespacedClient):
    @query_params('master_timeout', 'wait_for_completion')
    def create(self, repository, snapshot, body=None, params=None):
        """
        Create a snapshot in repository
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html>`_

        :arg repository: A repository name
        :arg snapshot: A snapshot name
        :arg body: The snapshot definition
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg wait_for_completion: Should this request wait until the operation
            has completed before returning, default False
        """
        for param in (repository, snapshot):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path('_snapshot',
            repository, snapshot), params=params, body=body)

    @query_params('master_timeout')
    def delete(self, repository, snapshot, params=None):
        """
        Deletes a snapshot from a repository.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html>`_

        :arg repository: A repository name
        :arg snapshot: A snapshot name
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        """
        for param in (repository, snapshot):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('DELETE',
            _make_path('_snapshot', repository, snapshot), params=params)

    @query_params('ignore_unavailable', 'master_timeout')
    def get(self, repository, snapshot, params=None):
        """
        Retrieve information about a snapshot.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html>`_

        :arg repository: A repository name
        :arg snapshot: A comma-separated list of snapshot names
        :arg ignore_unavailable: Whether to ignore unavailable snapshots,
            defaults to false which means a SnapshotMissingException is thrown
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        """
        for param in (repository, snapshot):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('GET', _make_path('_snapshot',
            repository, snapshot), params=params)

    @query_params('master_timeout', 'timeout')
    def delete_repository(self, repository, params=None):
        """
        Removes a shared file system repository.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html>`_

        :arg repository: A comma-separated list of repository names
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg timeout: Explicit operation timeout
        """
        if repository in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'repository'.")
        return self.transport.perform_request('DELETE',
            _make_path('_snapshot', repository), params=params)

    @query_params('local', 'master_timeout')
    def get_repository(self, repository=None, params=None):
        """
        Return information about registered repositories.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html>`_

        :arg repository: A comma-separated list of repository names
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        """
        return self.transport.perform_request('GET', _make_path('_snapshot',
            repository), params=params)

    @query_params('master_timeout', 'timeout', 'verify')
    def create_repository(self, repository, body, params=None):
        """
        Registers a shared file system repository.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html>`_

        :arg repository: A repository name
        :arg body: The repository definition
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg timeout: Explicit operation timeout
        :arg verify: Whether to verify the repository after creation
        """
        for param in (repository, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path('_snapshot',
            repository), params=params, body=body)

    @query_params('master_timeout', 'wait_for_completion')
    def restore(self, repository, snapshot, body=None, params=None):
        """
        Restore a snapshot.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html>`_

        :arg repository: A repository name
        :arg snapshot: A snapshot name
        :arg body: Details of what to restore
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg wait_for_completion: Should this request wait until the operation
            has completed before returning, default False
        """
        for param in (repository, snapshot):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('POST', _make_path('_snapshot',
            repository, snapshot, '_restore'), params=params, body=body)

    @query_params('ignore_unavailable', 'master_timeout')
    def status(self, repository=None, snapshot=None, params=None):
        """
        Return information about all currently running snapshots. By specifying
        a repository name, it's possible to limit the results to a particular
        repository.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html>`_

        :arg repository: A repository name
        :arg snapshot: A comma-separated list of snapshot names
        :arg ignore_unavailable: Whether to ignore unavailable snapshots,
            defaults to false which means a SnapshotMissingException is thrown
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        """
        return self.transport.perform_request('GET', _make_path('_snapshot',
            repository, snapshot, '_status'), params=params)

    @query_params('master_timeout', 'timeout')
    def verify_repository(self, repository, params=None):
        """
        Returns a list of nodes where repository was successfully verified or
        an error message if verification process failed.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-snapshots.html>`_

        :arg repository: A repository name
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg timeout: Explicit operation timeout
        """
        if repository in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'repository'.")
        return self.transport.perform_request('POST', _make_path('_snapshot',
            repository, '_verify'), params=params)
