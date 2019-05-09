from braintree.attribute_getter import AttributeGetter

class FundingDetails(AttributeGetter):
    detail_list = [
        "account_number_last_4",
        "routing_number",
        "destination",
        "email",
        "mobile_phone",
    ]

    def __init__(self, attributes):
        AttributeGetter.__init__(self, attributes)

    def __repr__(self):
        return super(FundingDetails, self).__repr__(self.detail_list)
