from __future__ import absolute_import, division, print_function

from stripe.api_resources.abstract import ListableAPIResource


class ReportType(ListableAPIResource):
    OBJECT_NAME = "reporting.report_type"
