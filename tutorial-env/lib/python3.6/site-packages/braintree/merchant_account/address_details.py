from braintree.attribute_getter import AttributeGetter

class AddressDetails(AttributeGetter):
    detail_list = [
        "street_address",
        "locality",
        "region",
        "postal_code",
    ]

    def __init__(self, attributes):
        AttributeGetter.__init__(self, attributes)

    def __repr__(self):
        return super(AddressDetails, self).__repr__(self.detail_list)
