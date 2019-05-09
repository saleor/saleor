from __future__ import absolute_import, division, print_function

from stripe.api_resources.abstract import ListableAPIResource


class ScheduledQueryRun(ListableAPIResource):
    OBJECT_NAME = "scheduled_query_run"

    @classmethod
    def class_url(cls):
        return "/v1/sigma/scheduled_query_runs"
