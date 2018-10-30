from ...account.forms import get_address_form
from ...account.models import Address


def get_field_name(field_name, parent_field_name):
    if not field_name:
        return None
    if not parent_field_name:
        return field_name
    return '%s:%s' % (parent_field_name, field_name)


class I18nMixin:
    """Mixin to be used with BaseMutation or ModelMutation, providing methods
    necessary to fulfill the internationalization process.
    """

    @classmethod
    def validate_address(
            cls, address_data, errors, parent_field_name=None,
            instance=None):
        address_form, _ = get_address_form(
            address_data, address_data['country'])
        if not address_form.is_valid():
            for field_name, field_errors in address_form.errors.items():
                error_field = get_field_name(field_name, parent_field_name)
                # sometimes same error is duplicated within the field errors
                for error_msg in set(field_errors):
                    cls.add_error(errors, error_field, error_msg)
            return None, errors
        if not instance:
            instance = Address()
        cls.construct_instance(instance, address_data)
        cls.clean_instance(instance, errors)
        return instance, errors
