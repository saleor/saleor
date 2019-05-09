from braintree.configuration import Configuration
from braintree.resource import Resource

class AccountUpdaterDailyReport(Resource):

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        if "report_url" in attributes:
            self.report_url = attributes.pop("report_url")
        if "report_date" in attributes:
            self.report_date = attributes.pop("report_date")

    def __repr__(self):
        detail_list = ["report_url", "report_date"]
        return super(AccountUpdaterDailyReport, self).__repr__(detail_list)
