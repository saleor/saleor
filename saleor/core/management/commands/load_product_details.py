import csv
import os

from django.core.management import BaseCommand, call_command
from django.utils.text import slugify

from saleor.channel.models import Channel
from saleor.product.models import ProductType, Product, Category, ProductVariant, \
    ProductVariantChannelListing
from saleor.tests.utils import dummy_editorjs

from saleor.attribute.models import Attribute, AttributeValue
from saleor.product.models import ProductChannelListing, Collection


class Command(BaseCommand):
    def read_csv(self, file_path):
        category = None
        product_variants = []
        products = []
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            for idx, row in enumerate(reader):
                if idx > 0:
                    if idx == 1:
                        category = row[1]
                        product_variants = row[6:]
                    else:
                        # create product schema
                        name_end = row[1].index(' Intense')
                        product = {
                            "name": row[1][12:name_end].strip(),
                            # classification + notes = description
                            "description": " ".join(row[1:2]),
                            "notes": {
                                "top": row[3].split(','),
                                "middle": row[4].split(','),
                                "base": row[5].split(',')
                            },
                            # create variants based on product_variants
                            # name = volume
                            # item code = sku
                            # price_amount = variant price
                            # channel 1 is default
                            # use price data for product variant channel listing
                            "variants": [
                                {"sku": f"{row[0]}-{cap.replace('ml', '')}",
                                 "name": cap,
                                 "price": row[6 + i].replace("R", "")} for i, cap in
                                enumerate(product_variants)
                            ]
                        }
                        products.append(product)
        return category, products

    def handle(self, *args, **options):
        call_command('loaddata', '/app/saleor/static/populatedb_data.json')
        file_path = os.path.join(os.getcwd(),
                                 'saleor/static/Website products update 16-11 Thur - Sheet1.csv')
        category_name, products = self.read_csv(file_path)
        product_type = ProductType.objects.get(slug="perfume")
        default_channel = Channel.objects.get(slug="default-channel")
        perfume_category = Category.objects.get(slug='perfume')
        scent_attribute = Attribute.objects.get(slug="scent")
        category, _ = Category.objects.update_or_create(name=category_name,
                                                     parent=perfume_category)
        for product in products:
            new_product, _ = Product.objects.update_or_create(
                product_type=product_type,
                category=category,
                name=product['name'],
                slug=slugify(product['name']),
                description=dummy_editorjs(product['description']),
                description_plaintext=product['description'],
                search_document=f"{product['name']}{product['description']}",
            )
            for note, scents in product["notes"].items():
                for scent in scents:
                    attribute_value, _ = AttributeValue.objects.update_or_create(
                        attribute=scent_attribute, slug=slugify(scent))
                    attribute_value.name = scent.strip()
                    attribute_value.save()
            product_listing, _ = ProductChannelListing.objects.update_or_create(
                product=new_product,
                channel=default_channel,
                currency='ZAR'
            )
            for variant in product['variants']:
                product_variant, _ = ProductVariant.objects.update_or_create(
                    product=new_product,
                    name=variant['name'],
                    sku=variant['sku']
                )
                variant_listing, _ = ProductVariantChannelListing.objects.update_or_create(
                    variant=product_variant,
                    channel=default_channel,
                    currency='ZAR',
                    price_amount=variant['price'],
                    cost_price_amount=0.9*float(variant['price'])
                )
