import datetime
from contextlib import contextmanager
from functools import partial
from io import BytesIO
from typing import Optional
from unittest.mock import MagicMock

import graphene
import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext as BaseCaptureQueriesContext
from freezegun import freeze_time
from PIL import Image

from ..account.models import Address, Group, StaffNotificationRecipient
from ..core import JobStatus
from ..core.models import EventDelivery, EventDeliveryAttempt, EventPayload
from ..core.payments import PaymentInterface
from ..csv.events import ExportEvents
from ..csv.models import ExportEvent, ExportFile
from ..discount import PromotionEvents
from ..discount.models import (
    PromotionEvent,
    PromotionRuleTranslation,
    PromotionTranslation,
    VoucherTranslation,
)
from ..payment.interface import AddressData
from ..permission.enums import get_permissions
from ..product.models import (
    CategoryTranslation,
    CollectionTranslation,
    ProductTranslation,
    ProductVariantTranslation,
)
from ..tax import TaxCalculationStrategy
from ..webhook.event_types import WebhookEventAsyncType
from ..webhook.transport.utils import to_payment_app_id
from .utils import dummy_editorjs


class CaptureQueriesContext(BaseCaptureQueriesContext):
    IGNORED_QUERIES = settings.PATTERNS_IGNORED_IN_QUERY_CAPTURES  # type: ignore[misc]

    @property
    def captured_queries(self):
        base_queries = self.connection.queries[
            self.initial_queries : self.final_queries
        ]
        new_queries = []

        def is_query_ignored(sql):
            for pattern in self.IGNORED_QUERIES:
                # Ignore the query if matches
                if pattern.match(sql):
                    return True
            return False

        for query in base_queries:
            if not is_query_ignored(query["sql"]):
                new_queries.append(query)

        return new_queries


def _assert_num_queries(context, *, config, num, exact=True, info=None):
    # Extracted from pytest_django.fixtures._assert_num_queries
    yield context

    verbose = config.getoption("verbose") > 0
    num_performed = len(context)

    if exact:
        failed = num != num_performed
    else:
        failed = num_performed > num

    if not failed:
        return

    msg = "Expected to perform {} queries {}{}".format(
        num,
        "" if exact else "or less ",
        "but {} done".format(
            num_performed == 1 and "1 was" or "%d were" % (num_performed,)
        ),
    )
    if info:
        msg += f"\n{info}"
    if verbose:
        sqls = (q["sql"] for q in context.captured_queries)
        msg += "\n\nQueries:\n========\n\n{}".format("\n\n".join(sqls))
    else:
        msg += " (add -v option to show queries)"
    pytest.fail(msg)


@pytest.fixture
def capture_queries(pytestconfig):
    cfg = pytestconfig

    @contextmanager
    def _capture_queries(
        num: Optional[int] = None, msg: Optional[str] = None, exact=False
    ):
        with CaptureQueriesContext(connection) as ctx:
            yield ctx
            if num is not None:
                _assert_num_queries(ctx, config=cfg, num=num, exact=exact, info=msg)

    return _capture_queries


@pytest.fixture
def assert_num_queries(capture_queries):
    return partial(capture_queries, exact=True)


@pytest.fixture
def assert_max_num_queries(capture_queries):
    return partial(capture_queries, exact=False)


@pytest.fixture
def address(db):  # pylint: disable=W0613
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        postal_code="53-601",
        country="PL",
        phone="+48713988102",
    )


@pytest.fixture
def address_with_areas(db):
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        postal_code="53-601",
        country="PL",
        phone="+48713988102",
        country_area="test_country_area",
        city_area="test_city_area",
    )


@pytest.fixture
def address_other_country():
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        street_address_1="4371 Lucas Knoll Apt. 791",
        city="BENNETTMOUTH",
        postal_code="13377",
        country="IS",
        phone="+40123123123",
    )


@pytest.fixture
def address_usa():
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        street_address_1="2000 Main Street",
        city="Irvine",
        postal_code="92614",
        country_area="CA",
        country="US",
        phone="",
    )


@pytest.fixture
def graphql_address_data():
    return {
        "firstName": "John Saleor",
        "lastName": "Doe Mirumee",
        "companyName": "Mirumee Software",
        "streetAddress1": "Tęczowa 7",
        "streetAddress2": "",
        "postalCode": "53-601",
        "country": "PL",
        "city": "Wrocław",
        "countryArea": "",
        "phone": "+48321321888",
        "metadata": [{"key": "public", "value": "public_value"}],
    }


@pytest.fixture
def graphql_address_data_skipped_validation(graphql_address_data):
    graphql_address_data["skipValidation"] = True
    return graphql_address_data


@pytest.fixture
def image():
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    return SimpleUploadedFile("product.jpg", img_data.getvalue())


@pytest.fixture
def icon_image():
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="PNG")
    return SimpleUploadedFile("logo.png", img_data.getvalue())


@pytest.fixture
def image_list():
    img_data_1 = BytesIO()
    image_1 = Image.new("RGB", size=(1, 1))
    image_1.save(img_data_1, format="JPEG")

    img_data_2 = BytesIO()
    image_2 = Image.new("RGB", size=(1, 1))
    image_2.save(img_data_2, format="JPEG")
    return [
        SimpleUploadedFile("image1.jpg", img_data_1.getvalue()),
        SimpleUploadedFile("image2.jpg", img_data_2.getvalue()),
    ]


@pytest.fixture
def dummy_address_data(address):
    return AddressData(
        first_name=address.first_name,
        last_name=address.last_name,
        company_name=address.company_name,
        street_address_1=address.street_address_1,
        street_address_2=address.street_address_2,
        city=address.city,
        city_area=address.city_area,
        postal_code=address.postal_code,
        country=address.country,
        country_area=address.country_area,
        phone=address.phone,
        metadata=address.metadata,
        private_metadata=address.private_metadata,
    )


@pytest.fixture
def dummy_webhook_app_payment_data(dummy_payment_data, payment_app):
    dummy_payment_data.gateway = to_payment_app_id(payment_app, "credit-card")
    return dummy_payment_data


@pytest.fixture
def promotion_events(catalogue_promotion, staff_user):
    promotion = catalogue_promotion
    rule_id = promotion.rules.first().pk
    events = PromotionEvent.objects.bulk_create(
        [
            PromotionEvent(
                type=PromotionEvents.PROMOTION_CREATED,
                user=staff_user,
                promotion=promotion,
            ),
            PromotionEvent(
                type=PromotionEvents.PROMOTION_UPDATED,
                user=staff_user,
                promotion=promotion,
            ),
            PromotionEvent(
                type=PromotionEvents.RULE_CREATED,
                user=staff_user,
                promotion=promotion,
                parameters={"rule_id": rule_id},
            ),
            PromotionEvent(
                type=PromotionEvents.RULE_UPDATED,
                user=staff_user,
                promotion=promotion,
                parameters={"rule_id": rule_id},
            ),
            PromotionEvent(
                type=PromotionEvents.RULE_DELETED,
                user=staff_user,
                promotion=promotion,
                parameters={"rule_id": rule_id},
            ),
            PromotionEvent(
                type=PromotionEvents.PROMOTION_STARTED,
                user=staff_user,
                promotion=promotion,
            ),
            PromotionEvent(
                type=PromotionEvents.PROMOTION_ENDED,
                user=staff_user,
                promotion=promotion,
            ),
        ]
    )
    return events


@pytest.fixture
def permission_group_manage_discounts(permission_manage_discounts, staff_users):
    group = Group.objects.create(
        name="Manage discounts group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_discounts)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_manage_orders(permission_manage_orders, staff_users):
    group = Group.objects.create(
        name="Manage orders group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_orders)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_manage_shipping(permission_manage_shipping, staff_users):
    group = Group.objects.create(
        name="Manage shipping group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_shipping)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_manage_users(permission_manage_users, staff_users):
    group = Group.objects.create(
        name="Manage user group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_users)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_manage_staff(permission_manage_staff, staff_users):
    group = Group.objects.create(
        name="Manage staff group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_staff)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_manage_apps(permission_manage_apps, staff_users):
    group = Group.objects.create(
        name="Manage apps group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_apps)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_handle_payments(permission_manage_payments, staff_users):
    group = Group.objects.create(
        name="Manage apps group.", restricted_access_to_channels=False
    )
    group.permissions.add(permission_manage_payments)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_all_perms_all_channels(
    permission_manage_users, staff_users, channel_USD, channel_PLN
):
    group = Group.objects.create(
        name="All permissions for all channels.",
        restricted_access_to_channels=False,
    )
    permissions = get_permissions()
    group.permissions.add(*permissions)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_no_perms_all_channels(staff_users, channel_USD, channel_PLN):
    group = Group.objects.create(
        name="All permissions for all channels.",
        restricted_access_to_channels=False,
    )
    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_all_perms_channel_USD_only(
    permission_manage_users, staff_users, channel_USD, channel_PLN
):
    group = Group.objects.create(
        name="All permissions for USD channel only.",
        restricted_access_to_channels=True,
    )
    permissions = get_permissions()
    group.permissions.add(*permissions)

    group.channels.add(channel_USD)

    group.user_set.add(staff_users[1])
    return group


@pytest.fixture
def permission_group_all_perms_without_any_channel(
    permission_manage_users, staff_users, channel_USD, channel_PLN
):
    group = Group.objects.create(
        name="All permissions without any channel access.",
        restricted_access_to_channels=True,
    )
    permissions = get_permissions()
    group.permissions.add(*permissions)
    return group


@pytest.fixture
def shop_permissions(
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_taxes,
    permission_manage_settings,
):
    return [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_taxes,
        permission_manage_settings,
    ]


@pytest.fixture
def voucher_translation_fr(voucher):
    return VoucherTranslation.objects.create(
        language_code="fr", voucher=voucher, name="French name"
    )


@pytest.fixture
def product_translation_fr(product):
    return ProductTranslation.objects.create(
        language_code="fr",
        product=product,
        name="French name",
        description=dummy_editorjs("French description."),
    )


@pytest.fixture
def variant_translation_fr(variant):
    return ProductVariantTranslation.objects.create(
        language_code="fr", product_variant=variant, name="French product variant name"
    )


@pytest.fixture
def collection_translation_fr(published_collection):
    return CollectionTranslation.objects.create(
        language_code="fr",
        collection=published_collection,
        name="French collection name",
        slug="french-collection-name",
        description=dummy_editorjs("French description."),
    )


@pytest.fixture
def category_translation_fr(category):
    return CategoryTranslation.objects.create(
        language_code="fr",
        category=category,
        name="French category name",
        description=dummy_editorjs("French category description."),
    )


@pytest.fixture
def category_translation_with_slug_pl(category):
    return CategoryTranslation.objects.create(
        language_code="pl",
        category=category,
        name="Polish category name",
        slug="polish-category-name",
        description=dummy_editorjs("Polish category description."),
    )


@pytest.fixture
def promotion_translation_fr(catalogue_promotion):
    return PromotionTranslation.objects.create(
        language_code="fr",
        promotion=catalogue_promotion,
        name="French promotion name",
        description=dummy_editorjs("French promotion description."),
    )


@pytest.fixture
def promotion_converted_from_sale_translation_fr(promotion_converted_from_sale):
    return PromotionTranslation.objects.create(
        language_code="fr",
        promotion=promotion_converted_from_sale,
        name="French sale name",
        description=dummy_editorjs("French sale description."),
    )


@pytest.fixture
def promotion_rule_translation_fr(promotion_rule):
    return PromotionRuleTranslation.objects.create(
        language_code="fr",
        promotion_rule=promotion_rule,
        name="French promotion rule name",
        description=dummy_editorjs("French promotion rule description."),
    )


@pytest.fixture
def media_root(tmpdir, settings):
    root = str(tmpdir.mkdir("media"))
    settings.MEDIA_ROOT = root
    return root


@pytest.fixture(scope="session", autouse=True)
def private_media_root(tmpdir_factory):
    return str(tmpdir_factory.mktemp("private-media"))


@pytest.fixture(autouse=True)
def private_media_setting(private_media_root, settings):
    settings.PRIVATE_MEDIA_ROOT = private_media_root
    return private_media_root


@pytest.fixture
def description_json():
    return {
        "blocks": [
            {
                "key": "",
                "data": {
                    "text": "E-commerce for the PWA era",
                },
                "text": "E-commerce for the PWA era",
                "type": "header-two",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {
                    "text": (
                        "A modular, high performance e-commerce storefront "
                        "built with GraphQL, Django, and ReactJS."
                    )
                },
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "",
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {
                    "text": (
                        "Saleor is a rapidly-growing open source e-commerce platform "
                        "that has served high-volume companies from branches "
                        "like publishing and apparel since 2012. Based on Python "
                        "and Django, the latest major update introduces a modular "
                        "front end with a GraphQL API and storefront and dashboard "
                        "written in React to make Saleor a full-functionality "
                        "open source e-commerce."
                    ),
                },
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {"text": ""},
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {
                    "text": "Get Saleor today!",
                },
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [{"key": 0, "length": 17, "offset": 0}],
                "inlineStyleRanges": [],
            },
        ],
        "entityMap": {
            "0": {
                "data": {"href": "https://github.com/mirumee/saleor"},
                "type": "LINK",
                "mutability": "MUTABLE",
            }
        },
    }


@pytest.fixture
def other_description_json():
    return {
        "blocks": [
            {
                "key": "",
                "data": {
                    "text": (
                        "A GRAPHQL-FIRST <b>ECOMMERCE</b> PLATFORM FOR PERFECTIONISTS"
                    ),
                },
                "text": "A GRAPHQL-FIRST ECOMMERCE PLATFORM FOR PERFECTIONISTS",
                "type": "header-two",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {
                    "text": (
                        "Saleor is powered by a GraphQL server running on "
                        "top of Python 3 and a Django 2 framework."
                    ),
                },
                "type": "paragraph",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
        ],
        "entityMap": {},
    }


@pytest.fixture
def tax_line_data_response():
    return {
        "id": "1234",
        "currency": "PLN",
        "unit_net_amount": 12.34,
        "unit_gross_amount": 12.34,
        "total_gross_amount": 12.34,
        "total_net_amount": 12.34,
        "tax_rate": 23,
    }


@pytest.fixture
def tax_data_response(tax_line_data_response):
    return {
        "currency": "PLN",
        "total_net_amount": 12.34,
        "total_gross_amount": 12.34,
        "subtotal_net_amount": 12.34,
        "subtotal_gross_amount": 12.34,
        "shipping_price_gross_amount": 12.34,
        "shipping_price_net_amount": 12.34,
        "shipping_tax_rate": 23,
        "lines": [tax_line_data_response] * 5,
    }


@pytest.fixture
def fake_payment_interface(mocker):
    return mocker.Mock(spec=PaymentInterface)


@pytest.fixture
def staff_notification_recipient(db, staff_user):
    return StaffNotificationRecipient.objects.create(active=True, user=staff_user)


@pytest.fixture(params=["warehouse_for_cc", "shipping_method"])
def delivery_method(request, warehouse_for_cc, shipping_method):
    if request.param == "warehouse":
        return warehouse_for_cc
    if request.param == "shipping_method":
        return shipping_method
    return None


@pytest.fixture
def user_export_file(staff_user):
    job = ExportFile.objects.create(user=staff_user)
    return job


@pytest.fixture
def app_export_file(app):
    job = ExportFile.objects.create(app=app)
    return job


@pytest.fixture
def removed_app_export_file(removed_app):
    job = ExportFile.objects.create(app=removed_app)
    return job


@pytest.fixture
def export_file_list(staff_user):
    export_file_list = list(
        ExportFile.objects.bulk_create(
            [
                ExportFile(user=staff_user),
                ExportFile(
                    user=staff_user,
                ),
                ExportFile(
                    user=staff_user,
                    status=JobStatus.SUCCESS,
                ),
                ExportFile(user=staff_user, status=JobStatus.SUCCESS),
                ExportFile(
                    user=staff_user,
                    status=JobStatus.FAILED,
                ),
            ]
        )
    )

    updated_date = datetime.datetime(2019, 4, 18, tzinfo=datetime.UTC)
    created_date = datetime.datetime(2019, 4, 10, tzinfo=datetime.UTC)
    new_created_and_updated_dates = [
        (created_date, updated_date),
        (created_date, updated_date + datetime.timedelta(hours=2)),
        (
            created_date + datetime.timedelta(hours=2),
            updated_date - datetime.timedelta(days=2),
        ),
        (created_date - datetime.timedelta(days=2), updated_date),
        (
            created_date - datetime.timedelta(days=5),
            updated_date - datetime.timedelta(days=5),
        ),
    ]
    for counter, export_file in enumerate(export_file_list):
        created, updated = new_created_and_updated_dates[counter]
        export_file.created_at = created
        export_file.updated_at = updated

    ExportFile.objects.bulk_update(export_file_list, ["created_at", "updated_at"])

    return export_file_list


@pytest.fixture
def user_export_event(user_export_file):
    return ExportEvent.objects.create(
        type=ExportEvents.EXPORT_FAILED,
        export_file=user_export_file,
        user=user_export_file.user,
        parameters={"message": "Example error message"},
    )


@pytest.fixture
def app_export_event(app_export_file):
    return ExportEvent.objects.create(
        type=ExportEvents.EXPORT_FAILED,
        export_file=app_export_file,
        app=app_export_file.app,
        parameters={"message": "Example error message"},
    )


@pytest.fixture
def removed_app_export_event(removed_app_export_file):
    return ExportEvent.objects.create(
        type=ExportEvents.EXPORT_FAILED,
        export_file=removed_app_export_file,
        app=removed_app_export_file.app,
        parameters={"message": "Example error message"},
    )


@pytest.fixture
def app_manifest():
    return {
        "name": "Sample Saleor App",
        "version": "0.1",
        "about": "Sample Saleor App serving as an example.",
        "dataPrivacy": "",
        "dataPrivacyUrl": "",
        "homepageUrl": "http://172.17.0.1:5000/homepageUrl",
        "supportUrl": "http://172.17.0.1:5000/supportUrl",
        "id": "saleor-complex-sample",
        "permissions": ["MANAGE_PRODUCTS", "MANAGE_USERS"],
        "appUrl": "",
        "configurationUrl": "http://127.0.0.1:5000/configuration/",
        "tokenTargetUrl": "http://127.0.0.1:5000/configuration/install",
    }


@pytest.fixture
def app_manifest_webhook():
    return {
        "name": "webhook",
        "asyncEvents": [
            "ORDER_CREATED",
            "ORDER_FULLY_PAID",
            "CUSTOMER_CREATED",
            "FULFILLMENT_CREATED",
        ],
        "query": """
            subscription {
                event {
                    ... on OrderCreated {
                        order {
                            id
                        }
                    }
                    ... on OrderFullyPaid {
                        order {
                            id
                        }
                    }
                    ... on CustomerCreated {
                        user {
                            id
                        }
                    }
                    ... on FulfillmentCreated {
                        fulfillment {
                            id
                        }
                    }
                }
            }
        """,
        "targetUrl": "https://app.example/api/webhook",
    }


@pytest.fixture
def event_payload():
    """Return event payload."""
    return EventPayload.objects.create_with_payload_file(
        payload='{"payload_key": "payload_value"}'
    )


@pytest.fixture
def event_delivery(event_payload, webhook, app):
    """Return an event delivery object."""
    return EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook,
    )


@pytest.fixture
def event_delivery_removed_app(event_payload, webhook_removed_app):
    return EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook_removed_app,
    )


@pytest.fixture
def event_attempt(event_delivery):
    """Return an event delivery attempt object."""
    return EventDeliveryAttempt.objects.create(
        delivery=event_delivery,
        task_id="example_task_id",
        duration=None,
        response="example_response",
        response_headers=None,
        request_headers=None,
    )


@pytest.fixture
def event_payload_in_database():
    """Return event payload with payload in database."""
    return EventPayload.objects.create(payload='{"payload_key": "payload_value"}')


@pytest.fixture
def event_delivery_payload_in_database(event_payload_in_database, webhook, app):
    """Return an event delivery object."""
    return EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload_in_database,
        webhook=webhook,
    )


@pytest.fixture
def event_attempt_payload_in_database(event_delivery_payload_in_database):
    """Return an event delivery attempt object."""
    return EventDeliveryAttempt.objects.create(
        delivery=event_delivery_payload_in_database,
        task_id="example_task_id",
        duration=None,
        response="example_response",
        response_headers=None,
        request_headers=None,
    )


@pytest.fixture
def webhook_list_stored_payment_methods_response():
    return {
        "paymentMethods": [
            {
                "id": "method-1",
                "supportedPaymentFlows": ["INTERACTIVE"],
                "type": "Credit Card",
                "creditCardInfo": {
                    "brand": "visa",
                    "lastDigits": "1234",
                    "expMonth": 1,
                    "expYear": 2023,
                    "firstDigits": "123456",
                },
                "name": "***1234",
                "data": {"some": "data"},
            }
        ]
    }


@pytest.fixture
def event_attempt_removed_app(event_delivery_removed_app):
    """Return event delivery attempt object"""  # noqa: D400, D415
    return EventDeliveryAttempt.objects.create(
        delivery=event_delivery_removed_app,
        task_id="example_task_id",
        duration=None,
        response="example_response",
        response_headers=None,
        request_headers=None,
    )


@pytest.fixture
def check_payment_balance_input():
    return {
        "gatewayId": "mirumee.payments.gateway",
        "channel": "channel_default",
        "method": "givex",
        "card": {
            "cvc": "9891",
            "code": "12345678910",
            "money": {"currency": "GBP", "amount": 100.0},
        },
    }


@pytest.fixture
def delivery_attempts(event_delivery):
    """Return consecutive delivery attempt IDs."""
    with freeze_time("2020-03-18 12:00:00"):
        attempt_1 = EventDeliveryAttempt.objects.create(
            delivery=event_delivery,
            task_id="example_task_id_1",
            duration=None,
            response="example_response",
            response_headers=None,
            request_headers=None,
        )

    with freeze_time("2020-03-18 13:00:00"):
        attempt_2 = EventDeliveryAttempt.objects.create(
            delivery=event_delivery,
            task_id="example_task_id_2",
            duration=None,
            response="example_response",
            response_headers=None,
            request_headers=None,
        )

    with freeze_time("2020-03-18 14:00:00"):
        attempt_3 = EventDeliveryAttempt.objects.create(
            delivery=event_delivery,
            task_id="example_task_id_3",
            duration=None,
            response="example_response",
            response_headers=None,
            request_headers=None,
        )

    attempt_1 = graphene.Node.to_global_id("EventDeliveryAttempt", attempt_1.pk)
    attempt_2 = graphene.Node.to_global_id("EventDeliveryAttempt", attempt_2.pk)
    attempt_3 = graphene.Node.to_global_id("EventDeliveryAttempt", attempt_3.pk)
    webhook_id = graphene.Node.to_global_id("Webhook", event_delivery.webhook.pk)

    return {
        "webhook_id": webhook_id,
        "attempt_1_id": attempt_1,
        "attempt_2_id": attempt_2,
        "attempt_3_id": attempt_3,
    }


@pytest.fixture
def event_deliveries(event_payload, webhook, app):
    """Return consecutive event delivery IDs."""
    delivery_1 = EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook,
    )
    delivery_2 = EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook,
    )
    delivery_3 = EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook,
    )
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    delivery_1 = graphene.Node.to_global_id("EventDelivery", delivery_1.pk)
    delivery_2 = graphene.Node.to_global_id("EventDelivery", delivery_2.pk)
    delivery_3 = graphene.Node.to_global_id("EventDelivery", delivery_3.pk)

    return {
        "webhook_id": webhook_id,
        "delivery_1_id": delivery_1,
        "delivery_2_id": delivery_2,
        "delivery_3_id": delivery_3,
    }


@pytest.fixture
def transaction_session_response():
    return {
        "pspReference": "psp-123",
        "data": {"some-json": "data"},
        "result": "CHARGE_SUCCESS",
        "amount": "10.00",
        "time": "2022-11-18T13:25:58.169685+00:00",
        "externalUrl": "http://127.0.0.1:9090/external-reference",
        "message": "Message related to the payment",
    }


class Info:
    def __init__(self, request):
        self.context = request


@pytest.fixture
def dummy_info(request):
    return Info(request)


@pytest.fixture
def async_subscription_webhooks_with_root_objects(
    subscription_account_deleted_webhook,
    subscription_account_confirmed_webhook,
    subscription_account_email_changed_webhook,
    subscription_account_set_password_requested_webhook,
    subscription_account_confirmation_requested_webhook,
    subscription_account_delete_requested_webhook,
    subscription_account_change_email_requested_webhook,
    subscription_staff_set_password_requested_webhook,
    subscription_address_created_webhook,
    subscription_address_updated_webhook,
    subscription_address_deleted_webhook,
    subscription_app_installed_webhook,
    subscription_app_updated_webhook,
    subscription_app_deleted_webhook,
    subscription_app_status_changed_webhook,
    subscription_attribute_created_webhook,
    subscription_attribute_updated_webhook,
    subscription_attribute_deleted_webhook,
    subscription_attribute_value_created_webhook,
    subscription_attribute_value_updated_webhook,
    subscription_attribute_value_deleted_webhook,
    subscription_category_created_webhook,
    subscription_category_updated_webhook,
    subscription_category_deleted_webhook,
    subscription_channel_created_webhook,
    subscription_channel_updated_webhook,
    subscription_channel_deleted_webhook,
    subscription_channel_status_changed_webhook,
    subscription_gift_card_created_webhook,
    subscription_gift_card_updated_webhook,
    subscription_gift_card_deleted_webhook,
    subscription_gift_card_sent_webhook,
    subscription_gift_card_status_changed_webhook,
    subscription_gift_card_metadata_updated_webhook,
    subscription_gift_card_export_completed_webhook,
    subscription_menu_created_webhook,
    subscription_menu_updated_webhook,
    subscription_menu_deleted_webhook,
    subscription_menu_item_created_webhook,
    subscription_menu_item_updated_webhook,
    subscription_menu_item_deleted_webhook,
    subscription_shipping_price_created_webhook,
    subscription_shipping_price_updated_webhook,
    subscription_shipping_price_deleted_webhook,
    subscription_shipping_zone_created_webhook,
    subscription_shipping_zone_updated_webhook,
    subscription_shipping_zone_deleted_webhook,
    subscription_shipping_zone_metadata_updated_webhook,
    subscription_product_updated_webhook,
    subscription_product_created_webhook,
    subscription_product_deleted_webhook,
    subscription_product_export_completed_webhook,
    subscription_product_media_updated_webhook,
    subscription_product_media_created_webhook,
    subscription_product_media_deleted_webhook,
    subscription_product_metadata_updated_webhook,
    subscription_product_variant_created_webhook,
    subscription_product_variant_updated_webhook,
    subscription_product_variant_deleted_webhook,
    subscription_product_variant_metadata_updated_webhook,
    subscription_product_variant_out_of_stock_webhook,
    subscription_product_variant_back_in_stock_webhook,
    subscription_order_created_webhook,
    subscription_order_updated_webhook,
    subscription_order_confirmed_webhook,
    subscription_order_fully_paid_webhook,
    subscription_order_refunded_webhook,
    subscription_order_fully_refunded_webhook,
    subscription_order_paid_webhook,
    subscription_order_cancelled_webhook,
    subscription_order_expired_webhook,
    subscription_order_fulfilled_webhook,
    subscription_order_metadata_updated_webhook,
    subscription_order_bulk_created_webhook,
    subscription_draft_order_created_webhook,
    subscription_draft_order_updated_webhook,
    subscription_draft_order_deleted_webhook,
    subscription_sale_created_webhook,
    subscription_sale_updated_webhook,
    subscription_sale_deleted_webhook,
    subscription_sale_toggle_webhook,
    subscription_invoice_requested_webhook,
    subscription_invoice_deleted_webhook,
    subscription_invoice_sent_webhook,
    subscription_fulfillment_canceled_webhook,
    subscription_fulfillment_created_webhook,
    subscription_fulfillment_approved_webhook,
    subscription_fulfillment_metadata_updated_webhook,
    subscription_fulfillment_tracking_number_updated,
    subscription_customer_created_webhook,
    subscription_customer_updated_webhook,
    subscription_customer_deleted_webhook,
    subscription_customer_metadata_updated_webhook,
    subscription_collection_created_webhook,
    subscription_collection_updated_webhook,
    subscription_collection_deleted_webhook,
    subscription_collection_metadata_updated_webhook,
    subscription_checkout_created_webhook,
    subscription_checkout_updated_webhook,
    subscription_checkout_fully_paid_webhook,
    subscription_checkout_metadata_updated_webhook,
    subscription_page_created_webhook,
    subscription_page_updated_webhook,
    subscription_page_deleted_webhook,
    subscription_page_type_created_webhook,
    subscription_page_type_updated_webhook,
    subscription_page_type_deleted_webhook,
    subscription_permission_group_created_webhook,
    subscription_permission_group_updated_webhook,
    subscription_permission_group_deleted_webhook,
    subscription_product_created_multiple_events_webhook,
    subscription_staff_created_webhook,
    subscription_staff_updated_webhook,
    subscription_staff_deleted_webhook,
    subscription_transaction_item_metadata_updated_webhook,
    subscription_translation_created_webhook,
    subscription_translation_updated_webhook,
    subscription_warehouse_created_webhook,
    subscription_warehouse_updated_webhook,
    subscription_warehouse_deleted_webhook,
    subscription_warehouse_metadata_updated_webhook,
    subscription_voucher_created_webhook,
    subscription_voucher_updated_webhook,
    subscription_voucher_deleted_webhook,
    subscription_voucher_codes_created_webhook,
    subscription_voucher_codes_deleted_webhook,
    subscription_voucher_webhook_with_meta,
    subscription_voucher_metadata_updated_webhook,
    subscription_voucher_code_export_completed_webhook,
    address,
    app,
    numeric_attribute,
    category,
    channel_PLN,
    gift_card,
    menu_item,
    shipping_method,
    product,
    fulfilled_order,
    fulfillment,
    stock,
    customer_user,
    collection,
    checkout,
    page,
    permission_group_manage_users,
    shipping_zone,
    staff_user,
    voucher,
    warehouse,
    translated_attribute,
    transaction_item_created_by_app,
    product_media_image,
    user_export_file,
    promotion_converted_from_sale,
):
    events = WebhookEventAsyncType
    attr = numeric_attribute
    attr_value = attr.values.first()
    menu = menu_item.menu
    order = fulfilled_order
    invoice = order.invoices.first()
    page_type = page.page_type
    transaction_item_created_by_app.use_old_id = True
    transaction_item_created_by_app.save()
    variant = product.variants.first()
    voucher_code = voucher.codes.first()

    return {
        events.ACCOUNT_DELETED: [
            subscription_account_deleted_webhook,
            customer_user,
        ],
        events.ACCOUNT_EMAIL_CHANGED: [
            subscription_account_email_changed_webhook,
            customer_user,
        ],
        events.ACCOUNT_CONFIRMED: [
            subscription_account_confirmed_webhook,
            customer_user,
        ],
        events.ACCOUNT_DELETE_REQUESTED: [
            subscription_account_delete_requested_webhook,
            customer_user,
        ],
        events.ACCOUNT_SET_PASSWORD_REQUESTED: [
            subscription_account_set_password_requested_webhook,
            customer_user,
        ],
        events.ACCOUNT_CHANGE_EMAIL_REQUESTED: [
            subscription_account_change_email_requested_webhook,
            customer_user,
        ],
        events.ACCOUNT_CONFIRMATION_REQUESTED: [
            subscription_account_confirmation_requested_webhook,
            customer_user,
        ],
        events.STAFF_SET_PASSWORD_REQUESTED: [
            subscription_staff_set_password_requested_webhook,
            staff_user,
        ],
        events.ADDRESS_UPDATED: [subscription_address_updated_webhook, address],
        events.ADDRESS_CREATED: [subscription_address_created_webhook, address],
        events.ADDRESS_DELETED: [subscription_address_deleted_webhook, address],
        events.APP_UPDATED: [subscription_app_updated_webhook, app],
        events.APP_DELETED: [subscription_app_deleted_webhook, app],
        events.APP_INSTALLED: [subscription_app_installed_webhook, app],
        events.APP_STATUS_CHANGED: [subscription_app_status_changed_webhook, app],
        events.ATTRIBUTE_CREATED: [subscription_attribute_created_webhook, attr],
        events.ATTRIBUTE_UPDATED: [subscription_attribute_updated_webhook, attr],
        events.ATTRIBUTE_DELETED: [subscription_attribute_deleted_webhook, attr],
        events.ATTRIBUTE_VALUE_UPDATED: [
            subscription_attribute_value_updated_webhook,
            attr_value,
        ],
        events.ATTRIBUTE_VALUE_CREATED: [
            subscription_attribute_value_created_webhook,
            attr_value,
        ],
        events.ATTRIBUTE_VALUE_DELETED: [
            subscription_attribute_value_deleted_webhook,
            attr_value,
        ],
        events.CATEGORY_CREATED: [subscription_category_created_webhook, category],
        events.CATEGORY_UPDATED: [subscription_category_updated_webhook, category],
        events.CATEGORY_DELETED: [subscription_category_deleted_webhook, category],
        events.CHANNEL_CREATED: [subscription_channel_created_webhook, channel_PLN],
        events.CHANNEL_UPDATED: [subscription_channel_updated_webhook, channel_PLN],
        events.CHANNEL_DELETED: [subscription_channel_deleted_webhook, channel_PLN],
        events.CHANNEL_STATUS_CHANGED: [
            subscription_channel_status_changed_webhook,
            channel_PLN,
        ],
        events.GIFT_CARD_CREATED: [subscription_gift_card_created_webhook, gift_card],
        events.GIFT_CARD_UPDATED: [subscription_gift_card_updated_webhook, gift_card],
        events.GIFT_CARD_DELETED: [subscription_gift_card_deleted_webhook, gift_card],
        events.GIFT_CARD_SENT: [subscription_gift_card_sent_webhook, gift_card],
        events.GIFT_CARD_STATUS_CHANGED: [
            subscription_gift_card_status_changed_webhook,
            gift_card,
        ],
        events.GIFT_CARD_METADATA_UPDATED: [
            subscription_gift_card_metadata_updated_webhook,
            gift_card,
        ],
        events.GIFT_CARD_EXPORT_COMPLETED: [
            subscription_gift_card_export_completed_webhook,
            user_export_file,
        ],
        events.MENU_CREATED: [subscription_menu_created_webhook, menu],
        events.MENU_UPDATED: [subscription_menu_updated_webhook, menu],
        events.MENU_DELETED: [subscription_menu_deleted_webhook, menu],
        events.MENU_ITEM_CREATED: [subscription_menu_item_created_webhook, menu_item],
        events.MENU_ITEM_UPDATED: [subscription_menu_item_updated_webhook, menu_item],
        events.MENU_ITEM_DELETED: [subscription_menu_item_deleted_webhook, menu_item],
        events.ORDER_CREATED: [subscription_order_created_webhook, order],
        events.ORDER_UPDATED: [subscription_order_updated_webhook, order],
        events.ORDER_CONFIRMED: [subscription_order_confirmed_webhook, order],
        events.ORDER_FULLY_PAID: [subscription_order_fully_paid_webhook, order],
        events.ORDER_PAID: [subscription_order_paid_webhook, order],
        events.ORDER_REFUNDED: [subscription_order_refunded_webhook, order],
        events.ORDER_FULLY_REFUNDED: [subscription_order_fully_refunded_webhook, order],
        events.ORDER_FULFILLED: [subscription_order_fulfilled_webhook, order],
        events.ORDER_CANCELLED: [subscription_order_cancelled_webhook, order],
        events.ORDER_EXPIRED: [subscription_order_expired_webhook, order],
        events.ORDER_METADATA_UPDATED: [
            subscription_order_metadata_updated_webhook,
            order,
        ],
        events.ORDER_BULK_CREATED: [subscription_order_bulk_created_webhook, order],
        events.DRAFT_ORDER_CREATED: [subscription_draft_order_created_webhook, order],
        events.DRAFT_ORDER_UPDATED: [subscription_draft_order_updated_webhook, order],
        events.DRAFT_ORDER_DELETED: [subscription_draft_order_deleted_webhook, order],
        events.PRODUCT_CREATED: [subscription_product_created_webhook, product],
        events.PRODUCT_UPDATED: [subscription_product_updated_webhook, product],
        events.PRODUCT_DELETED: [subscription_product_deleted_webhook, product],
        events.PRODUCT_EXPORT_COMPLETED: [
            subscription_product_export_completed_webhook,
            user_export_file,
        ],
        events.PRODUCT_MEDIA_CREATED: [
            subscription_product_media_created_webhook,
            product_media_image,
        ],
        events.PRODUCT_MEDIA_UPDATED: [
            subscription_product_media_updated_webhook,
            product_media_image,
        ],
        events.PRODUCT_MEDIA_DELETED: [
            subscription_product_media_deleted_webhook,
            product_media_image,
        ],
        events.PRODUCT_METADATA_UPDATED: [
            subscription_product_metadata_updated_webhook,
            product,
        ],
        events.PRODUCT_VARIANT_CREATED: [
            subscription_product_variant_created_webhook,
            variant,
        ],
        events.PRODUCT_VARIANT_UPDATED: [
            subscription_product_variant_updated_webhook,
            variant,
        ],
        events.PRODUCT_VARIANT_OUT_OF_STOCK: [
            subscription_product_variant_out_of_stock_webhook,
            stock,
        ],
        events.PRODUCT_VARIANT_BACK_IN_STOCK: [
            subscription_product_variant_back_in_stock_webhook,
            stock,
        ],
        events.PRODUCT_VARIANT_DELETED: [
            subscription_product_variant_deleted_webhook,
            variant,
        ],
        events.PRODUCT_VARIANT_METADATA_UPDATED: [
            subscription_product_variant_metadata_updated_webhook,
            variant,
        ],
        events.SALE_CREATED: [
            subscription_sale_created_webhook,
            promotion_converted_from_sale,
        ],
        events.SALE_UPDATED: [
            subscription_sale_updated_webhook,
            promotion_converted_from_sale,
        ],
        events.SALE_DELETED: [
            subscription_sale_deleted_webhook,
            promotion_converted_from_sale,
        ],
        events.SALE_TOGGLE: [
            subscription_sale_toggle_webhook,
            promotion_converted_from_sale,
        ],
        events.INVOICE_REQUESTED: [subscription_invoice_requested_webhook, invoice],
        events.INVOICE_DELETED: [subscription_invoice_deleted_webhook, invoice],
        events.INVOICE_SENT: [subscription_invoice_sent_webhook, invoice],
        events.FULFILLMENT_CANCELED: [
            subscription_fulfillment_canceled_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_CREATED: [
            subscription_fulfillment_created_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_APPROVED: [
            subscription_fulfillment_approved_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_METADATA_UPDATED: [
            subscription_fulfillment_metadata_updated_webhook,
            fulfillment,
        ],
        events.FULFILLMENT_TRACKING_NUMBER_UPDATED: [
            subscription_fulfillment_tracking_number_updated,
            fulfillment,
        ],
        events.CUSTOMER_CREATED: [subscription_customer_created_webhook, customer_user],
        events.CUSTOMER_UPDATED: [subscription_customer_updated_webhook, customer_user],
        events.CUSTOMER_METADATA_UPDATED: [
            subscription_customer_metadata_updated_webhook,
            customer_user,
        ],
        events.COLLECTION_CREATED: [
            subscription_collection_created_webhook,
            collection,
        ],
        events.COLLECTION_UPDATED: [
            subscription_collection_updated_webhook,
            collection,
        ],
        events.COLLECTION_DELETED: [
            subscription_collection_deleted_webhook,
            collection,
        ],
        events.COLLECTION_METADATA_UPDATED: [
            subscription_collection_metadata_updated_webhook,
            collection,
        ],
        events.CHECKOUT_CREATED: [subscription_checkout_created_webhook, checkout],
        events.CHECKOUT_UPDATED: [subscription_checkout_updated_webhook, checkout],
        events.CHECKOUT_FULLY_PAID: [
            subscription_checkout_fully_paid_webhook,
            checkout,
        ],
        events.CHECKOUT_METADATA_UPDATED: [
            subscription_checkout_metadata_updated_webhook,
            checkout,
        ],
        events.PAGE_CREATED: [subscription_page_created_webhook, page],
        events.PAGE_UPDATED: [subscription_page_updated_webhook, page],
        events.PAGE_DELETED: [subscription_page_deleted_webhook, page],
        events.PAGE_TYPE_CREATED: [subscription_page_type_created_webhook, page_type],
        events.PAGE_TYPE_UPDATED: [subscription_page_type_updated_webhook, page_type],
        events.PAGE_TYPE_DELETED: [subscription_page_type_deleted_webhook, page_type],
        events.PERMISSION_GROUP_CREATED: [
            subscription_permission_group_created_webhook,
            permission_group_manage_users,
        ],
        events.PERMISSION_GROUP_UPDATED: [
            subscription_permission_group_updated_webhook,
            permission_group_manage_users,
        ],
        events.PERMISSION_GROUP_DELETED: [
            subscription_permission_group_deleted_webhook,
            permission_group_manage_users,
        ],
        events.SHIPPING_PRICE_CREATED: [
            subscription_shipping_price_created_webhook,
            shipping_method,
        ],
        events.SHIPPING_PRICE_UPDATED: [
            subscription_shipping_price_updated_webhook,
            shipping_method,
        ],
        events.SHIPPING_PRICE_DELETED: [
            subscription_shipping_price_deleted_webhook,
            shipping_method,
        ],
        events.SHIPPING_ZONE_CREATED: [
            subscription_shipping_zone_created_webhook,
            shipping_zone,
        ],
        events.SHIPPING_ZONE_UPDATED: [
            subscription_shipping_zone_updated_webhook,
            shipping_zone,
        ],
        events.SHIPPING_ZONE_DELETED: [
            subscription_shipping_zone_deleted_webhook,
            shipping_zone,
        ],
        events.SHIPPING_ZONE_METADATA_UPDATED: [
            subscription_shipping_zone_metadata_updated_webhook,
            shipping_zone,
        ],
        events.STAFF_CREATED: [subscription_staff_created_webhook, staff_user],
        events.STAFF_UPDATED: [subscription_staff_updated_webhook, staff_user],
        events.STAFF_DELETED: [subscription_staff_deleted_webhook, staff_user],
        events.TRANSACTION_ITEM_METADATA_UPDATED: [
            subscription_transaction_item_metadata_updated_webhook,
            transaction_item_created_by_app,
        ],
        events.TRANSLATION_CREATED: [
            subscription_translation_created_webhook,
            translated_attribute,
        ],
        events.TRANSLATION_UPDATED: [
            subscription_translation_updated_webhook,
            translated_attribute,
        ],
        events.VOUCHER_CREATED: [subscription_voucher_created_webhook, voucher],
        events.VOUCHER_UPDATED: [subscription_voucher_updated_webhook, voucher],
        events.VOUCHER_DELETED: [subscription_voucher_deleted_webhook, voucher],
        events.VOUCHER_CODES_CREATED: [
            subscription_voucher_codes_created_webhook,
            voucher_code,
        ],
        events.VOUCHER_CODES_DELETED: [
            subscription_voucher_codes_deleted_webhook,
            voucher_code,
        ],
        events.VOUCHER_METADATA_UPDATED: [
            subscription_voucher_metadata_updated_webhook,
            voucher,
        ],
        events.VOUCHER_CODE_EXPORT_COMPLETED: [
            subscription_voucher_code_export_completed_webhook,
            user_export_file,
        ],
        events.WAREHOUSE_CREATED: [subscription_warehouse_created_webhook, warehouse],
        events.WAREHOUSE_UPDATED: [subscription_warehouse_updated_webhook, warehouse],
        events.WAREHOUSE_DELETED: [subscription_warehouse_deleted_webhook, warehouse],
        events.WAREHOUSE_METADATA_UPDATED: [
            subscription_warehouse_metadata_updated_webhook,
            warehouse,
        ],
    }


@pytest.fixture
def setup_mock_for_cache():
    """Mock cache backend.

    To be used together with `cache_mock` and `dummy_cache`, where:
    - `dummy_cache` is a dict the mock is write to, instead of real cache db
    - `cache_mock` is a patch applied on real cache db

    It supports following functions: `get`, `set`, `delete`, `incr` and `add`. If other
    function is utilised in a tested codebase, this fixture should be extended.

    Stores `key`, `value` and `ttl` in following format:
    {key: {"value": value, "ttl": ttl}}
    """

    def _mocked_cache(dummy_cache, cache_mock):
        def cache_get(key):
            if data := dummy_cache.get(key):
                return data["value"]
            return None

        def cache_set(key, value, timeout):
            dummy_cache.update({key: {"value": value, "ttl": timeout}})

        def cache_add(key, value, timeout):
            if dummy_cache.get(key) is None:
                dummy_cache.update({key: {"value": value, "ttl": timeout}})
                return True
            return False

        def cache_delete(key):
            dummy_cache.pop(key, None)

        def cache_incr(key, delta):
            if current_data := dummy_cache.get(key):
                current_value = current_data["value"]
                new_value = current_value + delta
                dummy_cache.update(
                    {key: {"value": new_value, "ttl": current_data["ttl"]}}
                )
                return new_value
            return None

        mocked_get_cache = MagicMock()
        mocked_set_cache = MagicMock()
        mocked_add_cache = MagicMock()
        mocked_incr_cache = MagicMock()
        mocked_delete_cache = MagicMock()

        mocked_get_cache.side_effect = cache_get
        mocked_set_cache.side_effect = cache_set
        mocked_add_cache.side_effect = cache_add
        mocked_incr_cache.side_effect = cache_incr
        mocked_delete_cache.side_effect = cache_delete

        cache_mock.get = mocked_get_cache
        cache_mock.set = mocked_set_cache
        cache_mock.add = mocked_add_cache
        cache_mock.incr = mocked_incr_cache
        cache_mock.delete = mocked_delete_cache

    return _mocked_cache


@pytest.fixture
def tax_configuration_flat_rates(channel_USD):
    tc = channel_USD.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.tax_app_id = "avatax.app"
    tc.save()
    return tc


@pytest.fixture
def tax_configuration_tax_app(channel_USD):
    tc = channel_USD.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.TAX_APP
    tc.tax_app_id = "avatax.app"
    tc.save()
    return tc
