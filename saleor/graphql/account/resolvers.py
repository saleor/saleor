from itertools import chain
from typing import Optional

from django.contrib.auth import models as auth_models
from i18naddress import get_validation_rules

from ...account import models
from ...core.exceptions import PermissionDenied
from ...core.permissions import AccountPermissions
from ...core.tracing import traced_resolver
from ...payment import gateway
from ...payment.utils import fetch_customer_id
from ..core.utils import from_global_id_or_error
from ..utils import format_permissions_for_display, get_user_or_app_from_context
from .types import Address, AddressValidationData, ChoiceValue, User
from .utils import (
    get_allowed_fields_camel_case,
    get_required_fields_camel_case,
    get_upper_fields_camel_case,
    get_user_permissions,
)

USER_SEARCH_FIELDS = (
    "email",
    "first_name",
    "last_name",
    "default_shipping_address__first_name",
    "default_shipping_address__last_name",
    "default_shipping_address__city",
    "default_shipping_address__country",
)


def resolve_customers(info, **_kwargs):
    return models.User.objects.customers()


def resolve_permission_group(id):
    return auth_models.Group.objects.filter(id=id).first()


def resolve_permission_groups(info, **_kwargs):
    return auth_models.Group.objects.all()


def resolve_staff_users(info, **_kwargs):
    return models.User.objects.staff()


@traced_resolver
def resolve_user(info, id=None, email=None):
    requester = get_user_or_app_from_context(info.context)
    if requester:
        filter_kwargs = {}
        if id:
            _model, filter_kwargs["pk"] = from_global_id_or_error(id, User)
        if email:
            filter_kwargs["email"] = email
        if requester.has_perms(
            [AccountPermissions.MANAGE_STAFF, AccountPermissions.MANAGE_USERS]
        ):
            return models.User.objects.filter(**filter_kwargs).first()
        if requester.has_perm(AccountPermissions.MANAGE_STAFF):
            return models.User.objects.staff().filter(**filter_kwargs).first()
        if requester.has_perm(AccountPermissions.MANAGE_USERS):
            return models.User.objects.customers().filter(**filter_kwargs).first()
    return PermissionDenied()


@traced_resolver
def resolve_address_validation_rules(
    info,
    country_code: str,
    country_area: Optional[str],
    city: Optional[str],
    city_area: Optional[str],
):

    params = {
        "country_code": country_code,
        "country_area": country_area,
        "city": city,
        "city_area": city_area,
    }
    rules = get_validation_rules(params)
    return AddressValidationData(
        country_code=rules.country_code,
        country_name=rules.country_name,
        address_format=rules.address_format,
        address_latin_format=rules.address_latin_format,
        allowed_fields=get_allowed_fields_camel_case(rules.allowed_fields),
        required_fields=get_required_fields_camel_case(rules.required_fields),
        upper_fields=get_upper_fields_camel_case(rules.upper_fields),
        country_area_type=rules.country_area_type,
        country_area_choices=[
            ChoiceValue(area[0], area[1]) for area in rules.country_area_choices
        ],
        city_type=rules.city_type,
        city_choices=[ChoiceValue(area[0], area[1]) for area in rules.city_choices],
        city_area_type=rules.city_area_type,
        city_area_choices=[
            ChoiceValue(area[0], area[1]) for area in rules.city_area_choices
        ],
        postal_code_type=rules.postal_code_type,
        postal_code_matchers=[
            compiled.pattern for compiled in rules.postal_code_matchers
        ],
        postal_code_examples=rules.postal_code_examples,
        postal_code_prefix=rules.postal_code_prefix,
    )


@traced_resolver
def resolve_payment_sources(info, user: models.User, channel_slug: str):
    manager = info.context.plugins
    stored_customer_accounts = (
        (gtw.id, fetch_customer_id(user, gtw.id))
        for gtw in gateway.list_gateways(manager, channel_slug)
    )
    return list(
        chain(
            *[
                prepare_graphql_payment_sources_type(
                    gateway.list_payment_sources(
                        gtw, customer_id, manager, channel_slug
                    )
                )
                for gtw, customer_id in stored_customer_accounts
                if customer_id is not None
            ]
        )
    )


def prepare_graphql_payment_sources_type(payment_sources):
    sources = []
    for src in payment_sources:
        sources.append(
            {
                "gateway": src.gateway,
                "payment_method_id": src.id,
                "credit_card_info": {
                    "last_digits": src.credit_card_info.last_4,
                    "exp_year": src.credit_card_info.exp_year,
                    "exp_month": src.credit_card_info.exp_month,
                    "brand": src.credit_card_info.brand,
                    "first_digits": src.credit_card_info.first_4,
                },
            }
        )
    return sources


@traced_resolver
def resolve_address(info, id):
    user = info.context.user
    app = info.context.app
    _model, address_pk = from_global_id_or_error(id, Address)
    if app and app.has_perm(AccountPermissions.MANAGE_USERS):
        return models.Address.objects.filter(pk=address_pk).first()
    if user and not user.is_anonymous:
        return user.addresses.filter(id=address_pk).first()
    return PermissionDenied()


def resolve_permissions(root: models.User):
    permissions = get_user_permissions(root)
    permissions = permissions.order_by("codename")
    return format_permissions_for_display(permissions)
