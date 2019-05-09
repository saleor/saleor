from braintree.successful_result import SuccessfulResult
from braintree.error_result import ErrorResult
from braintree.resource import Resource
from braintree.configuration import Configuration

class Address(Resource):
    """
    A class representing Braintree Address objects.

    An example of creating an address with all available fields::

        customer = braintree.Customer.create().customer
        result = braintree.Address.create({
            "customer_id": customer.id,
            "first_name": "John",
            "last_name": "Doe",
            "company": "Braintree",
            "street_address": "111 First Street",
            "extended_address": "Apartment 1",
            "locality": "Chicago",
            "region": "IL",
            "postal_code": "60606",
            "country_name": "United States of America"
        })

        print(result.customer.first_name)
        print(result.customer.last_name)
    """

    def __repr__(self):
        detail_list = [
            "customer_id",
            "company",
            "country_code_alpha2",
            "country_code_alpha3",
            "country_code_numeric",
            "country_name",
            "extended_address",
            "first_name",
            "last_name",
            "locality",
            "postal_code",
            "region",
            "street_address",
        ]
        return super(Address, self).__repr__(detail_list)


    @staticmethod
    def create(params={}):
        """
        Create an Address.

        A customer_id is required::

            customer = braintree.Customer.create().customer
            result = braintree.Address.create({
                "customer_id": customer.id,
                "first_name": "John",
                ...
            })

        """

        return Configuration.gateway().address.create(params)

    @staticmethod
    def delete(customer_id, address_id):
        """
        Delete an address

        Given a customer_id and address_id::

            result = braintree.Address.delete("my_customer_id", "my_address_id")

        """

        return Configuration.gateway().address.delete(customer_id, address_id)

    @staticmethod
    def find(customer_id, address_id):
        """
        Find an address, given a customer_id and address_id. This does not return
        a result object. This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided
        customer_id/address_id are not found. ::

            address = braintree.Address.find("my_customer_id", "my_address_id")
        """
        return Configuration.gateway().address.find(customer_id, address_id)

    @staticmethod
    def update(customer_id, address_id, params={}):
        """
        Update an existing Address.

        A customer_id and address_id are required::

            result = braintree.Address.update("my_customer_id", "my_address_id", {
                "first_name": "John"
            })

        """

        return Configuration.gateway().address.update(customer_id, address_id, params)

    @staticmethod
    def create_signature():
        return ["company", "country_code_alpha2", "country_code_alpha3", "country_code_numeric",
                "country_name", "customer_id", "extended_address", "first_name",
                "last_name", "locality", "postal_code", "region", "street_address"]

    @staticmethod
    def update_signature():
        return Address.create_signature()
