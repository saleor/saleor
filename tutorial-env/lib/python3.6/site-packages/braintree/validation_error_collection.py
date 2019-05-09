from braintree.validation_error import ValidationError

class ValidationErrorCollection(object):
    """
    A class representing a collection of validation errors.

    For more information on ValidationErrors, see https://developers.braintreepayments.com/reference/general/validation-errors/overview/python

    """

    def __init__(self, data={"errors": []}):
        self.data = data

    @property
    def deep_errors(self):
        """
        Return all :class:`ValidationErrors <braintree.validation_error.ValidationError>`, including nested errors.
        """

        result = []
        result.extend(self.errors)
        for nested_error in self.__nested_errors.values():
            result.extend(nested_error.deep_errors)
        return result

    def for_index(self, index):
        return self.for_object("index_%s" % index)

    def for_object(self, nested_key):
        """
        Returns a :class:`ValidationErrorCollection <braintree.validation_error_collection.ValidationErrorCollection>`

        It represents the errors at the nested level:::

            error_result = Transaction.sale({"credit_card": {"number": "invalid"}})
            print error_result.errors.for_object("transaction").for_object("credit_card").on("number")[0].code

        """

        return self.__get_nested_errors(nested_key)

    def on(self, attribute):
        """
        Returns the list of errors

        Restricted to a given attribute::

            error_result = Transaction.sale({"credit_card": {"number": "invalid"}})
            print [ error.code for error in error_result.errors.for_object("transaction").for_object("credit_card").on("number") ]

        """
        return [error for error in self.errors if error.attribute == attribute]

    @property
    def deep_size(self):
        """Returns the number of errors on this object and any nested objects."""

        size = len(self.errors)
        for error in self.__nested_errors.values():
            size += error.deep_size
        return size

    @property
    def errors(self):
        """Returns a list of :class:`ValidationError <braintree.validation_error.ValidationError>` objects."""

        return [ValidationError(error) for error in self.data["errors"]]

    @property
    def size(self):
        """Returns the number of errors on this object, without counting nested errors."""
        return len(self.errors)

    def __get_nested_errors(self, nested_key):
        if nested_key in self.__nested_errors:
            return self.__nested_errors[nested_key]
        else:
            return ValidationErrorCollection()

    def __getitem__(self, index):
        return self.errors[index]

    def __len__(self):
        return self.size

    @property
    def __nested_errors(self):
        nested_errors = {}
        for key in self.data:
            if key == "errors": continue
            nested_errors[key] = ValidationErrorCollection(self.data[key])
        return nested_errors

