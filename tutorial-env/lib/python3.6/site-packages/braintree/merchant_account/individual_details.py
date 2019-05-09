from braintree.attribute_getter import AttributeGetter
from braintree.merchant_account.address_details import AddressDetails

class IndividualDetails(AttributeGetter):
    detail_list = [
        "first_name",
        "last_name",
        "email",
        "phone",
        "date_of_birth",
        "ssn_last_4",
        "address_details",
    ]

    def __init__(self, attributes):
        AttributeGetter.__init__(self, attributes)
        self.address_details = AddressDetails(attributes.get("address", {}))

    def __repr__(self):
        return super(IndividualDetails, self).__repr__(self.detail_list)
