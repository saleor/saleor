from itertools import chain
from typing import Optional

import graphene
import graphene_django_optimizer as gql_optimizer
from graphql_jwt.exceptions import PermissionDenied
from i18naddress import get_validation_rules

from ...account import models
from ...payment import gateway
from ...payment.utils import fetch_customer_id
from ..utils import filter_by_query_param
from .types import AddressValidationData, ChoiceValue
from .utils import get_allowed_fields_camel_case, get_required_fields_camel_case

USER_SEARCH_FIELDS = (
    "email",
    "first_name",
    "last_name",
    "default_shipping_address__first_name",
    "default_shipping_address__last_name",
    "default_shipping_address__city",
    "default_shipping_address__country",
)


def resolve_customers(info, query):
    qs = models.User.objects.customers()
    qs = filter_by_query_param(
        queryset=qs, query=query, search_fields=USER_SEARCH_FIELDS
    )
    qs = qs.order_by("email")
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)


def resolve_staff_users(info, query):
    qs = models.User.objects.staff()
    qs = filter_by_query_param(
        queryset=qs, query=query, search_fields=USER_SEARCH_FIELDS
    )
    qs = qs.order_by("email")
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)


def resolve_user(info, id):
    requester = info.context.user or info.context.service_account
    if requester:
        _model, user_pk = graphene.Node.from_global_id(id)
        if requester.has_perms(["account.manage_staff", "account.manage_users"]):
            return models.User.objects.filter(pk=user_pk).first()
        if requester.has_perm("account.manage_staff"):
            return models.User.objects.staff().filter(pk=user_pk).first()
        if requester.has_perm("account.manage_users"):
            return models.User.objects.customers().filter(pk=user_pk).first()
    return PermissionDenied()


def resolve_service_accounts(info):
    qs = models.ServiceAccount.objects.all()
    return gql_optimizer.query(qs, info)


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
        upper_fields=rules.upper_fields,
        country_area_type=rules.country_area_type,
        country_area_choices=[
            ChoiceValue(area[0], area[1]) for area in rules.country_area_choices
        ],
        city_type=rules.city_type,
        city_choices=[ChoiceValue(area[0], area[1]) for area in rules.city_choices],
        city_area_type=rules.city_type,
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


def resolve_payment_sources(user: models.User):
    stored_customer_accounts = (
        (gtw["name"], fetch_customer_id(user, gtw["name"]))
        for gtw in gateway.list_gateways()
    )
    return list(
        chain(
            *[
                prepare_graphql_payment_sources_type(
                    gateway.list_payment_sources(gtw, customer_id)
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
                "credit_card_info": {
                    "last_digits": src.credit_card_info.last_4,
                    "exp_year": src.credit_card_info.exp_year,
                    "exp_month": src.credit_card_info.exp_month,
                    "brand": "",
                    "first_digits": "",
                },
            }
        )
    return sources
