from elasticsearch.client.utils import NamespacedClient, query_params, _make_path, SKIP_IN_PATH

class MlClient(NamespacedClient):
    @query_params('from_', 'size')
    def get_filters(self, filter_id=None, params=None):
        """

        :arg filter_id: The ID of the filter to fetch
        :arg from_: skips a number of filters
        :arg size: specifies a max number of filters to get
        """
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'filters', filter_id), params=params)

    @query_params()
    def get_datafeeds(self, datafeed_id=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-get-datafeed.html>`_

        :arg datafeed_id: The ID of the datafeeds to fetch
        """
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'datafeeds', datafeed_id), params=params)

    @query_params()
    def get_datafeed_stats(self, datafeed_id=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-get-datafeed-stats.html>`_

        :arg datafeed_id: The ID of the datafeeds stats to fetch
        """
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'datafeeds', datafeed_id, '_stats'), params=params)

    @query_params('anomaly_score', 'desc', 'end', 'exclude_interim', 'expand',
        'from_', 'size', 'sort', 'start')
    def get_buckets(self, job_id, timestamp=None, body=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-get-bucket.html>`_

        :arg job_id: ID of the job to get bucket results from
        :arg timestamp: The timestamp of the desired single bucket result
        :arg body: Bucket selection details if not provided in URI
        :arg anomaly_score: Filter for the most anomalous buckets
        :arg desc: Set the sort direction
        :arg end: End time filter for buckets
        :arg exclude_interim: Exclude interim results
        :arg expand: Include anomaly records
        :arg from_: skips a number of buckets
        :arg size: specifies a max number of buckets to get
        :arg sort: Sort buckets by a particular field
        :arg start: Start time filter for buckets
        """
        if job_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'job_id'.")
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, 'results', 'buckets', timestamp),
            params=params, body=body)

    @query_params('reset_end', 'reset_start')
    def post_data(self, job_id, body, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-post-data.html>`_

        :arg job_id: The name of the job receiving the data
        :arg body: The data to process
        :arg reset_end: Optional parameter to specify the end of the bucket
            resetting range
        :arg reset_start: Optional parameter to specify the start of the bucket
            resetting range
        """
        for param in (job_id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, '_data'), params=params,
            body=self._bulk_body(body))

    @query_params('force', 'timeout')
    def stop_datafeed(self, datafeed_id, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-stop-datafeed.html>`_

        :arg datafeed_id: The ID of the datafeed to stop
        :arg force: True if the datafeed should be forcefully stopped.
        :arg timeout: Controls the time to wait until a datafeed has stopped.
            Default to 20 seconds
        """
        if datafeed_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'datafeed_id'.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'datafeeds', datafeed_id, '_stop'), params=params)

    @query_params()
    def get_jobs(self, job_id=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-get-job.html>`_

        :arg job_id: The ID of the jobs to fetch
        """
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id), params=params)

    @query_params()
    def delete_expired_data(self, params=None):
        """
        """
        return self.transport.perform_request('DELETE',
            '/_xpack/ml/_delete_expired_data', params=params)

    @query_params()
    def put_job(self, job_id, body, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-put-job.html>`_

        :arg job_id: The ID of the job to create
        :arg body: The job
        """
        for param in (job_id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id), params=params, body=body)

    @query_params()
    def validate_detector(self, body, params=None):
        """

        :arg body: The detector
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('POST',
            '/_xpack/ml/anomaly_detectors/_validate/detector', params=params,
            body=body)

    @query_params('end', 'start', 'timeout')
    def start_datafeed(self, datafeed_id, body=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-start-datafeed.html>`_

        :arg datafeed_id: The ID of the datafeed to start
        :arg body: The start datafeed parameters
        :arg end: The end time when the datafeed should stop. When not set, the
            datafeed continues in real time
        :arg start: The start time from where the datafeed should begin
        :arg timeout: Controls the time to wait until a datafeed has started.
            Default to 20 seconds
        """
        if datafeed_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'datafeed_id'.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'datafeeds', datafeed_id, '_start'), params=params, body=body)

    @query_params('desc', 'end', 'exclude_interim', 'from_', 'record_score',
        'size', 'sort', 'start')
    def get_records(self, job_id, body=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-get-record.html>`_

        :arg job_id: None
        :arg body: Record selection criteria
        :arg desc: Set the sort direction
        :arg end: End time filter for records
        :arg exclude_interim: Exclude interim results
        :arg from_: skips a number of records
        :arg record_score:
        :arg size: specifies a max number of records to get
        :arg sort: Sort records by a particular field
        :arg start: Start time filter for records
        """
        if job_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'job_id'.")
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, 'results', 'records'), params=params,
            body=body)

    @query_params()
    def update_job(self, job_id, body, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-update-job.html>`_

        :arg job_id: The ID of the job to create
        :arg body: The job update settings
        """
        for param in (job_id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, '_update'), params=params, body=body)

    @query_params()
    def put_filter(self, filter_id, body, params=None):
        """

        :arg filter_id: The ID of the filter to create
        :arg body: The filter details
        """
        for param in (filter_id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path('_xpack', 'ml',
            'filters', filter_id), params=params, body=body)

    @query_params()
    def update_datafeed(self, datafeed_id, body, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-update-datafeed.html>`_

        :arg datafeed_id: The ID of the datafeed to update
        :arg body: The datafeed update settings
        """
        for param in (datafeed_id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'datafeeds', datafeed_id, '_update'), params=params, body=body)

    @query_params()
    def preview_datafeed(self, datafeed_id, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-preview-datafeed.html>`_

        :arg datafeed_id: The ID of the datafeed to preview
        """
        if datafeed_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'datafeed_id'.")
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'datafeeds', datafeed_id, '_preview'), params=params)

    @query_params('advance_time', 'calc_interim', 'end', 'skip_time', 'start')
    def flush_job(self, job_id, body=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-flush-job.html>`_

        :arg job_id: The name of the job to flush
        :arg body: Flush parameters
        :arg advance_time: Advances time to the given value generating results
            and updating the model for the advanced interval
        :arg calc_interim: Calculates interim results for the most recent bucket
            or all buckets within the latency period
        :arg end: When used in conjunction with calc_interim, specifies the
            range of buckets on which to calculate interim results
        :arg skip_time: Skips time to the given value without generating results
            or updating the model for the skipped interval
        :arg start: When used in conjunction with calc_interim, specifies the
            range of buckets on which to calculate interim results
        """
        if job_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'job_id'.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, '_flush'), params=params, body=body)

    @query_params('force', 'timeout')
    def close_job(self, job_id, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-close-job.html>`_

        :arg job_id: The name of the job to close
        :arg force: True if the job should be forcefully closed
        :arg timeout: Controls the time to wait until a job has closed. Default
            to 30 minutes
        """
        if job_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'job_id'.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, '_close'), params=params)

    @query_params()
    def open_job(self, job_id, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-open-job.html>`_

        :arg job_id: The ID of the job to open
        """
        if job_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'job_id'.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, '_open'), params=params)

    @query_params('force')
    def delete_job(self, job_id, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-delete-job.html>`_

        :arg job_id: The ID of the job to delete
        :arg force: True if the job should be forcefully deleted
        """
        if job_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'job_id'.")
        return self.transport.perform_request('DELETE', _make_path('_xpack',
            'ml', 'anomaly_detectors', job_id), params=params)

    @query_params('duration', 'expires_in')
    def forecast_job(self, job_id, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-forecast.html>`_

        :arg job_id: The name of the job to close
        :arg duration: A period of time that indicates how far into the future to forecast
        :arg expires_in: The period of time that forecast results are retained.
        """
        if job_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'job_id'.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, '_forecast'), params=params)

    @query_params()
    def update_model_snapshot(self, job_id, snapshot_id, body, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-update-snapshot.html>`_

        :arg job_id: The ID of the job to fetch
        :arg snapshot_id: The ID of the snapshot to update
        :arg body: The model snapshot properties to update
        """
        for param in (job_id, snapshot_id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, 'model_snapshots', snapshot_id,
            '_update'), params=params, body=body)

    @query_params()
    def delete_filter(self, filter_id, params=None):
        """

        :arg filter_id: The ID of the filter to delete
        """
        if filter_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'filter_id'.")
        return self.transport.perform_request('DELETE', _make_path('_xpack',
            'ml', 'filters', filter_id), params=params)

    @query_params()
    def validate(self, body, params=None):
        """

        :arg body: The job config
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('POST',
            '/_xpack/ml/anomaly_detectors/_validate', params=params, body=body)

    @query_params('from_', 'size')
    def get_categories(self, job_id, category_id=None, body=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-get-category.html>`_

        :arg job_id: The name of the job
        :arg category_id: The identifier of the category definition of interest
        :arg body: Category selection details if not provided in URI
        :arg from_: skips a number of categories
        :arg size: specifies a max number of categories to get
        """
        if job_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'job_id'.")
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, 'results', 'categories', category_id),
            params=params, body=body)

    @query_params('desc', 'end', 'exclude_interim', 'from_', 'influencer_score',
        'size', 'sort', 'start')
    def get_influencers(self, job_id, body=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-get-influencer.html>`_

        :arg job_id: None
        :arg body: Influencer selection criteria
        :arg desc: whether the results should be sorted in decending order
        :arg end: end timestamp for the requested influencers
        :arg exclude_interim: Exclude interim results
        :arg from_: skips a number of influencers
        :arg influencer_score: influencer score threshold for the requested
            influencers
        :arg size: specifies a max number of influencers to get
        :arg sort: sort field for the requested influencers
        :arg start: start timestamp for the requested influencers
        """
        if job_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'job_id'.")
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, 'results', 'influencers'),
            params=params, body=body)

    @query_params()
    def put_datafeed(self, datafeed_id, body, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-put-datafeed.html>`_

        :arg datafeed_id: The ID of the datafeed to create
        :arg body: The datafeed config
        """
        for param in (datafeed_id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path('_xpack', 'ml',
            'datafeeds', datafeed_id), params=params, body=body)

    @query_params('force')
    def delete_datafeed(self, datafeed_id, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-delete-datafeed.html>`_

        :arg datafeed_id: The ID of the datafeed to delete
        :arg force: True if the datafeed should be forcefully deleted
        """
        if datafeed_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'datafeed_id'.")
        return self.transport.perform_request('DELETE', _make_path('_xpack',
            'ml', 'datafeeds', datafeed_id), params=params)

    @query_params()
    def get_job_stats(self, job_id=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-get-job-stats.html>`_

        :arg job_id: The ID of the jobs stats to fetch
        """
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, '_stats'), params=params)

    @query_params('delete_intervening_results')
    def revert_model_snapshot(self, job_id, snapshot_id, body=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-revert-snapshot.html>`_

        :arg job_id: The ID of the job to fetch
        :arg snapshot_id: The ID of the snapshot to revert to
        :arg body: Reversion options
        :arg delete_intervening_results: Should we reset the results back to the
            time of the snapshot?
        """
        for param in (job_id, snapshot_id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('POST', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, 'model_snapshots', snapshot_id,
            '_revert'), params=params, body=body)

    @query_params('desc', 'end', 'from_', 'size', 'sort', 'start')
    def get_model_snapshots(self, job_id, snapshot_id=None, body=None, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-get-snapshot.html>`_

        :arg job_id: The ID of the job to fetch
        :arg snapshot_id: The ID of the snapshot to fetch
        :arg body: Model snapshot selection criteria
        :arg desc: True if the results should be sorted in descending order
        :arg end: The filter 'end' query parameter
        :arg from_: Skips a number of documents
        :arg size: The default number of documents returned in queries as a
            string.
        :arg sort: Name of the field to sort on
        :arg start: The filter 'start' query parameter
        """
        if job_id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'job_id'.")
        return self.transport.perform_request('GET', _make_path('_xpack', 'ml',
            'anomaly_detectors', job_id, 'model_snapshots', snapshot_id),
            params=params, body=body)

    @query_params()
    def delete_model_snapshot(self, job_id, snapshot_id, params=None):
        """

        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/ml-delete-snapshot.html>`_

        :arg job_id: The ID of the job to fetch
        :arg snapshot_id: The ID of the snapshot to delete
        """
        for param in (job_id, snapshot_id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('DELETE', _make_path('_xpack',
            'ml', 'anomaly_detectors', job_id, 'model_snapshots', snapshot_id),
            params=params)

