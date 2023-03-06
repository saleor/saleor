from itertools import chain
from typing import Optional

from django.db.models import Q
from i18naddress import get_validation_rules

from ...account import models
from ...core.exceptions import PermissionDenied
from ...core.permissions import (
    AccountPermissions,
    AuthorizationFilters,
    OrderPermissions,
    has_one_of_permissions,
)
from ...payment import gateway
from ...payment.utils import fetch_customer_id
from ..core import ResolveInfo
from ..core.tracing import traced_resolver
from ..core.utils import from_global_id_or_error
from ..meta.resolvers import resolve_metadata
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


def resolve_customers(_info):
    return models.User.objects.customers()


def resolve_permission_group(id):
    return models.Group.objects.filter(id=id).first()


def resolve_permission_groups(_info):
    return models.Group.objects.all()


def resolve_staff_users(_info):
    return models.User.objects.staff()


@traced_resolver
def resolve_user(info, id=None, email=None, external_reference=None):
    requester = get_user_or_app_from_context(info.context)
    if requester:
        filter_kwargs = {}
        if id:
            _model, filter_kwargs["pk"] = from_global_id_or_error(id, User)
        if email:
            filter_kwargs["email"] = email
        if external_reference:
            filter_kwargs["external_reference"] = external_reference
        if requester.has_perms(
            [AccountPermissions.MANAGE_STAFF, AccountPermissions.MANAGE_USERS]
        ):
            return models.User.objects.filter(**filter_kwargs).first()
        if requester.has_perm(AccountPermissions.MANAGE_STAFF):
            return models.User.objects.staff().filter(**filter_kwargs).first()
        if has_one_of_permissions(
            requester, [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
        ):
            return models.User.objects.customers().filter(**filter_kwargs).first()
    return PermissionDenied(
        permissions=[
            AccountPermissions.MANAGE_STAFF,
            AccountPermissions.MANAGE_USERS,
            OrderPermissions.MANAGE_ORDERS,
        ]
    )


@traced_resolver
def resolve_users(info, ids=None, emails=None):
    requester = get_user_or_app_from_context(info.context)
    if not requester:
        return models.User.objects.none()

    if requester.has_perms(
        [AccountPermissions.MANAGE_STAFF, AccountPermissions.MANAGE_USERS]
    ):
        qs = models.User.objects.all()
    elif requester.has_perm(AccountPermissions.MANAGE_STAFF):
        qs = models.User.objects.staff()
    elif requester.has_perm(AccountPermissions.MANAGE_USERS):
        qs = models.User.objects.customers()
    elif requester.id:
        # If user has no access to all users, we can only return themselves, but
        # only if they are authenticated and one of requested users
        qs = models.User.objects.filter(id=requester.id)
    else:
        qs = models.User.objects.none()

    if ids:
        ids = {from_global_id_or_error(id, User, raise_error=True)[1] for id in ids}

    if ids and emails:
        return qs.filter(Q(id__in=ids) | Q(email__in=emails))
    elif ids:
        return qs.filter(id__in=ids)
    return qs.filter(email__in=emails)


@traced_resolver
def resolve_address_validation_rules(
    info: ResolveInfo,
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
def resolve_payment_sources(_info, user: models.User, manager, channel_slug: str):
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
                "metadata": resolve_metadata(src.metadata),
            }
        )
    return sources


@traced_resolver
def resolve_address(info, id, app):
    user = info.context.user
    _, address_pk = from_global_id_or_error(id, Address)
    if app and app.has_perm(AccountPermissions.MANAGE_USERS):
        return models.Address.objects.filter(pk=address_pk).first()
    if user:
        return user.addresses.filter(id=address_pk).first()
    raise PermissionDenied(
        permissions=[AccountPermissions.MANAGE_USERS, AuthorizationFilters.OWNER]
    )


def resolve_addresses(info, ids, app):
    user = info.context.user
    ids = [
        from_global_id_or_error(address_id, Address, raise_error=True)[1]
        for address_id in ids
    ]
    if app and app.has_perm(AccountPermissions.MANAGE_USERS):
        return models.Address.objects.filter(id__in=ids)
    if user:
        return user.addresses.filter(id__in=ids)
    return models.Address.objects.none()


def resolve_permissions(root: models.User):
    permissions = get_user_permissions(root)
    permissions = permissions.order_by("codename")
    return format_permissions_for_display(permissions)
