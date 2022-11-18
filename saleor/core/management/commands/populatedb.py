from io import StringIO

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from ....account.utils import create_superuser
from ...utils.random_data import (
    add_address_to_admin,
    create_channels,
    create_checkout_with_custom_prices,
    create_checkout_with_preorders,
    create_checkout_with_same_variant_in_multiple_lines,
    create_gift_cards,
    create_menus,
    create_orders,
    create_page_type,
    create_pages,
    create_permission_groups,
    create_product_sales,
    create_products_by_schema,
    create_shipping_zones,
    create_staffs,
    create_tax_classes,
    create_users,
    create_vouchers,
    create_warehouses,
)


class Command(BaseCommand):
    help = "Populate database with test objects"
    placeholders_dir = "saleor/static/placeholders/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--createsuperuser",
            action="store_true",
            dest="createsuperuser",
            default=False,
            help="Create admin account",
        )
        parser.add_argument("--user_password", type=str, default="password")
        parser.add_argument("--staff_password", type=str, default="password")
        parser.add_argument("--superuser_password", type=str, default="admin")
        parser.add_argument(
            "--withoutimages",
            action="store_true",
            dest="withoutimages",
            default=False,
            help="Don't create product images",
        )
        parser.add_argument(
            "--skipsequencereset",
            action="store_true",
            dest="skipsequencereset",
            default=False,
            help="Don't reset SQL sequences that are out of sync.",
        )

    def sequence_reset(self):
        """Run a SQL sequence reset on all saleor.* apps.

        When a value is manually assigned to an auto-incrementing field
        it doesn't update the field's sequence, which might cause a conflict
        later on.
        """
        commands = StringIO()
        for app in apps.get_app_configs():
            if "saleor" in app.name:
                call_command(
                    "sqlsequencereset", app.label, stdout=commands, no_color=True
                )
        with connection.cursor() as cursor:
            cursor.execute(commands.getvalue())

    def handle(self, *args, **options):
        # set only our custom plugin to not call external API when preparing
        # example database
        user_password = options["user_password"]
        staff_password = options["staff_password"]
        superuser_password = options["superuser_password"]
        settings.PLUGINS = [
            "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin",
            "saleor.payment.gateways.dummy_credit_card.plugin."
            "DummyCreditCardGatewayPlugin",
        ]
        create_images = not options["withoutimages"]
        for msg in create_channels():
            self.stdout.write(msg)
        for msg in create_shipping_zones():
            self.stdout.write(msg)
        create_warehouses()
        self.stdout.write("Created warehouses")
        for msg in create_page_type():
            self.stdout.write(msg)
        for msg in create_pages():
            self.stdout.write(msg)
        create_products_by_schema(self.placeholders_dir, create_images)
        self.stdout.write("Created products")
        for msg in create_product_sales(2):
            self.stdout.write(msg)
        for msg in create_vouchers():
            self.stdout.write(msg)
        for msg in create_users(user_password, 20):
            self.stdout.write(msg)
        for msg in create_orders(20):
            self.stdout.write(msg)
        for msg in create_gift_cards():
            self.stdout.write(msg)
        for msg in create_menus():
            self.stdout.write(msg)
        for msg in create_checkout_with_preorders():
            self.stdout.write(msg)
        for msg in create_checkout_with_custom_prices():
            self.stdout.write(msg)
        for msg in create_tax_classes():
            self.stdout.write(msg)
        for msg in create_checkout_with_same_variant_in_multiple_lines():
            self.stdout.write(msg)

        if options["createsuperuser"]:
            credentials = {
                "email": "admin@example.com",
                "password": superuser_password,
            }
            msg = create_superuser(credentials)
            self.stdout.write(msg)
            add_address_to_admin(credentials["email"])
        if not options["skipsequencereset"]:
            self.sequence_reset()

        for msg in create_permission_groups(staff_password):
            self.stdout.write(msg)
        for msg in create_staffs(staff_password):
            self.stdout.write(msg)
