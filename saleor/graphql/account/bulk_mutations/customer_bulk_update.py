from collections import defaultdict
from copy import copy

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q
from graphene.utils.str_converters import to_camel_case

from ....account import models
from ....account.events import CustomerEvents
from ....checkout import AddressType
from ....core.tracing import traced_atomic_transaction
from ....giftcard.utils import assign_user_gift_cards
from ....order.utils import match_orders_with_new_user
from ....permission.enums import AccountPermissions
from ...core.descriptions import ADDED_IN_312, PREVIEW_FEATURE
from ...core.enums import CustomerBulkUpdateErrorCode, ErrorPolicyEnum
from ...core.mutations import BaseMutation, ModelMutation
from ...core.types import CustomerBulkUpdateError, NonNullList
from ...core.utils import get_duplicated_values
from ...core.validators import validate_one_of_args_is_in_mutation
from ...plugins.dataloaders import get_app_promise, get_plugin_manager_promise
from ..i18n import I18nMixin
from ..mutations.base import BILLING_ADDRESS_FIELD, SHIPPING_ADDRESS_FIELD
from ..mutations.staff import CustomerInput
from ..types import User


class CustomerBulkResult(graphene.ObjectType):
    customer = graphene.Field(User, required=False, description="Customer data.")
    errors = NonNullList(
        CustomerBulkUpdateError,
        required=False,
        description="List of errors occurred on update attempt.",
    )


class CustomerBulkUpdateInput(graphene.InputObjectType):
    id = graphene.ID(description="ID of a customer to update.", required=False)
    external_reference = graphene.String(
        required=False,
        description="External ID of a customer to update.",
    )
    input = CustomerInput(
        description="Fields required to update a customer.", required=True
    )


class CustomerBulkUpdate(BaseMutation, I18nMixin):
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were created.",
    )
    results = NonNullList(
        CustomerBulkResult,
        required=True,
        default_value=[],
        description="List of the updated customers.",
    )

    class Arguments:
        customers = NonNullList(
            CustomerBulkUpdateInput,
            required=True,
            description="Input list of customers to update.",
        )
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.value,
            description=(
                "Policies of error handling. DEFAULT: "
                + ErrorPolicyEnum.REJECT_EVERYTHING.name
            ),
        )

    class Meta:
        description = "Updates customers." + ADDED_IN_312 + PREVIEW_FEATURE
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = CustomerBulkUpdateError

    @classmethod
    def format_errors(cls, index, errors, index_error_map, field_prefix=None):
        for key, value in errors.error_dict.items():
            for e in value:
                path = (
                    to_camel_case(f"{field_prefix}.{key}")
                    if field_prefix
                    else to_camel_case(key)
                )
                index_error_map[index].append(
                    CustomerBulkUpdateError(
                        path=f"input.{path}",
                        message=e.messages[0],
                        code=e.code,
                    )
                )

    @classmethod
    def validate_customer(
        cls, customer_id, external_ref, cleaned_input, index, index_error_map
    ):
        errors_count = 0
        try:
            validate_one_of_args_is_in_mutation(
                "id",
                customer_id,
                "external_reference",
                external_ref,
                use_camel_case=True,
            )
        except ValidationError as exc:
            index_error_map[index].append(
                CustomerBulkUpdateError(
                    message=exc.message,
                    code=CustomerBulkUpdateErrorCode.INVALID.value,
                )
            )
            errors_count += 1

        if customer_id:
            try:
                type, customer_id = graphene.Node.from_global_id(customer_id)
                if type != "User":
                    index_error_map[index].append(
                        CustomerBulkUpdateError(
                            path="id",
                            message="Invalid customer ID.",
                            code=CustomerBulkUpdateErrorCode.INVALID.value,
                        )
                    )
                    errors_count += 1
                else:
                    cleaned_input["id"] = customer_id
            except Exception:
                index_error_map[index].append(
                    CustomerBulkUpdateError(
                        path="id",
                        message="Invalid customer ID.",
                        code=CustomerBulkUpdateErrorCode.INVALID.value,
                    )
                )
                errors_count += 1
        return errors_count

    @classmethod
    def clean_address(
        cls,
        address_data,
        address_type,
        field,
        index,
        index_error_map,
        format_check=True,
        required_check=True,
        enable_normalization=True,
    ):
        try:
            address_form = cls.validate_address_form(
                address_data,
                address_type,
                format_check=format_check,
                required_check=required_check,
                enable_normalization=enable_normalization,
            )

            return address_form.cleaned_data
        except ValidationError as exc:
            cls.format_errors(index, exc, index_error_map, field_prefix=field)

    @classmethod
    def clean_customers(cls, info, customers_input, index_error_map):
        cleaned_inputs_map: dict = {}

        external_refs = [
            customer_input["input"]["external_reference"]
            for customer_input in customers_input
            if customer_input["input"].get("external_reference")
        ]

        emails = [
            customer_input["input"]["email"].lower()
            for customer_input in customers_input
            if customer_input["input"].get("email")
        ]

        duplicated_refs = get_duplicated_values(external_refs)
        duplicated_emails = get_duplicated_values(emails)

        for index, customer_input in enumerate(customers_input):
            base_error_count = 0
            customer_id = customer_input.get("id")
            customer_external_ref = customer_input.get("external_reference")

            shipping_address_data = customer_input["input"].pop(
                SHIPPING_ADDRESS_FIELD, None
            )
            billing_address_data = customer_input["input"].pop(
                BILLING_ADDRESS_FIELD, None
            )

            customer_input["input"] = ModelMutation.clean_input(
                info, None, customer_input["input"], input_cls=CustomerInput
            )

            new_external_ref = customer_input["input"].get("external_reference")

            base_error_count += cls.validate_customer(
                customer_id,
                customer_external_ref,
                customer_input,
                index,
                index_error_map,
            )

            if new_external_ref in duplicated_refs:
                message = "Duplicated externalReference value."
                index_error_map[index].append(
                    CustomerBulkUpdateError(
                        path="input.externalReference",
                        message=message,
                        code=CustomerBulkUpdateErrorCode.DUPLICATED_INPUT_ITEM.value,
                    )
                )
                base_error_count += 1

            if shipping_address_data:
                clean_shipping_address = cls.clean_address(
                    shipping_address_data,
                    address_type=AddressType.SHIPPING,
                    field=SHIPPING_ADDRESS_FIELD,
                    index=index,
                    index_error_map=index_error_map,
                )
                customer_input["input"][SHIPPING_ADDRESS_FIELD] = clean_shipping_address

            if billing_address_data:
                clean_billing_address = cls.clean_address(
                    billing_address_data,
                    address_type=AddressType.BILLING,
                    field=BILLING_ADDRESS_FIELD,
                    index=index,
                    index_error_map=index_error_map,
                )
                customer_input["input"][BILLING_ADDRESS_FIELD] = clean_billing_address

            if email := customer_input.get("email"):
                customer_input["email"] = email.lower()

                if customer_input["email"] in duplicated_emails:
                    message = "Duplicated email value."
                    code = CustomerBulkUpdateErrorCode.DUPLICATED_INPUT_ITEM.value
                    index_error_map[index].append(
                        CustomerBulkUpdateError(
                            path="input.email", message=message, code=code
                        )
                    )
                    base_error_count += 1

            if base_error_count > 0:
                cleaned_inputs_map[index] = None
            else:
                cleaned_inputs_map[index] = customer_input

        return cleaned_inputs_map

    @classmethod
    def get_customers(cls, cleaned_inputs_map: dict) -> list[models.User]:
        lookup = Q()
        for customer_input in cleaned_inputs_map.values():
            if not customer_input:
                continue

            single_customer_lookup = Q()

            if customer_id := customer_input.get("id"):
                single_customer_lookup |= Q(pk=customer_id)
            else:
                single_customer_lookup |= Q(
                    external_reference=customer_input.get("external_reference")
                )
            lookup |= single_customer_lookup

        customers = models.User.objects.filter(lookup, is_staff=False)

        return list(customers)

    @classmethod
    def _get_customer(cls, customer_id, external_ref):
        if customer_id:
            return lambda customer: str(customer.id) == customer_id
        else:
            return lambda customer: customer.external_reference == external_ref

    @classmethod
    def update_address(cls, info, instance, data, field):
        address = cls.construct_instance(getattr(instance, field), data)
        cls.clean_instance(info, address)
        return address

    @classmethod
    def update_customers(cls, info, cleaned_inputs_map, index_error_map):
        instances_data_and_errors_list: list = []
        customers_list = cls.get_customers(cleaned_inputs_map)

        for index, cleaned_input in cleaned_inputs_map.items():
            if not cleaned_input:
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
                continue

            customer_id = cleaned_input.get("id")
            external_ref = cleaned_input.get("external_reference")
            data = cleaned_input["input"]
            shipping_address_input = data.pop(SHIPPING_ADDRESS_FIELD, None)
            billing_address_input = data.pop(BILLING_ADDRESS_FIELD, None)

            filter_customer = list(
                filter(
                    cls._get_customer(customer_id, external_ref),
                    customers_list,
                )
            )
            if filter_customer:
                try:
                    shipping_address = None
                    billing_address = None

                    old_instance = filter_customer[0]
                    new_instance = cls.construct_instance(copy(old_instance), data)
                    cls.clean_instance(info, new_instance)

                    if shipping_address_input:
                        shipping_address = cls.update_address(
                            info,
                            new_instance,
                            shipping_address_input,
                            SHIPPING_ADDRESS_FIELD,
                        )
                    if billing_address_input:
                        billing_address = cls.update_address(
                            info,
                            new_instance,
                            billing_address_input,
                            BILLING_ADDRESS_FIELD,
                        )

                    instances_data_and_errors_list.append(
                        {
                            "instance": new_instance,
                            "old_instance": old_instance,
                            "errors": index_error_map[index],
                            SHIPPING_ADDRESS_FIELD: shipping_address,
                            BILLING_ADDRESS_FIELD: billing_address,
                        }
                    )
                except ValidationError as exc:
                    cls.format_errors(index, exc, index_error_map)
                    instances_data_and_errors_list.append(
                        {"instance": None, "errors": index_error_map[index]}
                    )
            else:
                index_error_map[index].append(
                    CustomerBulkUpdateError(
                        message="Customer was not found.",
                        code=CustomerBulkUpdateErrorCode.NOT_FOUND.value,
                    )
                )
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )

        return instances_data_and_errors_list

    @classmethod
    def save_customers(cls, instances_data_with_errors_list):
        old_instances = []
        customers_to_update = []
        address_to_update = []

        for customer_data in instances_data_with_errors_list:
            customer = customer_data["instance"]

            if not customer:
                continue

            customers_to_update.append(customer)
            old_instances.append(customer_data["old_instance"])

            if shipping_address := customer_data[SHIPPING_ADDRESS_FIELD]:
                address_to_update.append(shipping_address)
            if billing_address := customer_data[BILLING_ADDRESS_FIELD]:
                address_to_update.append(billing_address)

        models.User.objects.bulk_update(
            customers_to_update,
            fields=[
                "first_name",
                "last_name",
                "email",
                "is_active",
                "note",
                "language_code",
                "external_reference",
                "updated_at",
            ],
        )

        models.Address.objects.bulk_update(
            address_to_update,
            fields=[
                "first_name",
                "last_name",
                "company_name",
                "street_address_1",
                "street_address_2",
                "city",
                "city_area",
                "postal_code",
                "country",
                "country_area",
                "phone",
            ],
        )

        return customers_to_update, old_instances

    @classmethod
    def post_save_actions(cls, info, instances, old_instances):
        customer_events = []
        manager = get_plugin_manager_promise(info.context).get()
        app = get_app_promise(info.context).get()
        staff_user = info.context.user

        for updated_instance, old_instance in zip(instances, old_instances):
            cls.call_event(manager.customer_updated, updated_instance)
            new_email = updated_instance.email
            new_fullname = updated_instance.get_full_name()

            # Compare the data
            has_new_name = old_instance.get_full_name() != new_fullname
            has_new_email = old_instance.email != new_email
            was_activated = not old_instance.is_active and updated_instance.is_active
            was_deactivated = old_instance.is_active and not updated_instance.is_active

            # Generate the events accordingly
            if has_new_email:
                customer_events.append(
                    models.CustomerEvent(
                        user=staff_user,
                        app=app,
                        order=None,
                        type=CustomerEvents.EMAIL_ASSIGNED,
                        parameters={"message": new_email},
                    )
                )
                assign_user_gift_cards(updated_instance)
                match_orders_with_new_user(updated_instance)

            if has_new_name:
                customer_events.append(
                    models.CustomerEvent(
                        user=staff_user,
                        app=app,
                        order=None,
                        type=CustomerEvents.NAME_ASSIGNED,
                        parameters={"message": new_fullname},
                    )
                )
            if was_activated:
                customer_events.append(
                    models.CustomerEvent(
                        user=staff_user,
                        app=app,
                        type=CustomerEvents.ACCOUNT_ACTIVATED,
                        parameters={"account_id": updated_instance.id},
                    )
                )
            if was_deactivated:
                customer_events.append(
                    models.CustomerEvent(
                        user=staff_user,
                        app=app,
                        type=CustomerEvents.ACCOUNT_DEACTIVATED,
                        parameters={"account_id": updated_instance.id},
                    )
                )

        models.CustomerEvent.objects.bulk_create(customer_events)

    @classmethod
    def get_results(cls, instances_data_with_errors_list, reject_everything=False):
        if reject_everything:
            return [
                CustomerBulkResult(customer=None, errors=data.get("errors"))
                for data in instances_data_with_errors_list
            ]
        return [
            CustomerBulkResult(customer=data.get("instance"), errors=data.get("errors"))
            if data.get("instance")
            else CustomerBulkResult(customer=None, errors=data.get("errors"))
            for data in instances_data_with_errors_list
        ]

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        error_policy = data["error_policy"]
        index_error_map: dict = defaultdict(list)

        cleaned_inputs_map = cls.clean_customers(
            info, data["customers"], index_error_map
        )

        instances_data_with_errors_list = cls.update_customers(
            info, cleaned_inputs_map, index_error_map
        )

        if any([True if error else False for error in index_error_map.values()]):
            if error_policy == ErrorPolicyEnum.REJECT_EVERYTHING.value:
                results = cls.get_results(instances_data_with_errors_list, True)
                return CustomerBulkUpdate(count=0, results=results)

            if error_policy == ErrorPolicyEnum.REJECT_FAILED_ROWS.value:
                for data in instances_data_with_errors_list:
                    if data["errors"] and data["instance"]:
                        data["instance"] = None

        updated_customers, old_instances = cls.save_customers(
            instances_data_with_errors_list
        )

        # prepare and return data
        results = cls.get_results(instances_data_with_errors_list)

        cls.post_save_actions(info, updated_customers, old_instances)

        return CustomerBulkUpdate(count=len(updated_customers), results=results)
