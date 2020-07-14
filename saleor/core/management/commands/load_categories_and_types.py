import csv

from django.core.management.base import BaseCommand

from saleor.product.models import Category, ProductType, Attribute, AttributeProduct
from django.utils.text import slugify


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='category file path')

    def handle(self, *args, **options):

        self.load_categories_and_types(options['path'])

    @staticmethod
    def load_categories_and_types(path):

        quality_attribute = Attribute.objects.get(slug='jakosc')
        color_attribute = Attribute.objects.get(slug='kolor')
        size_attribute = Attribute.objects.get(slug='rozmiar')
        material_attribute = Attribute.objects.get(slug='material')
        brand_attribute: Attribute

        with open(path, encoding="utf8", errors='ignore') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for rid, row in enumerate(reader):
                category_path = ""
                for elId, el in enumerate(row):

                    if elId == 0 and el != '':

                        try:
                            slug = slugify(row[0])
                            category_path += "/"
                            category_path += slug
                            category = Category.objects.get(name=row[0])
                            print('Kategoria istnieje: ', category)
                        except Category.DoesNotExist:
                            Category.objects.create(name=row[0], slug=slug)

                    if elId == 1 and el != '':

                        try:
                            slug = slugify(row[0] + " " + row[1])
                            category_path += "/"
                            category_path += slug
                            category = Category.objects.get(
                                name=row[1], parent=Category.objects.get(name=row[0]))
                            print('Kategoria istnieje: ', category)
                        except Category.DoesNotExist:
                            Category.objects.create(
                                name=row[1], slug=slug,
                                parent=Category.objects.get(name=row[0]))

                    if elId == 2 and el != '':
                        try:
                            slug = slugify(row[1] + " " + row[2])
                            category_path += "/"
                            category_path += slug
                            category = Category.objects.get(
                                name=row[2], parent=Category.objects.get(name=row[1]))
                            print('Kategoria istnieje: ', category)
                        except Category.DoesNotExist:
                            Category.objects.create(
                                name=row[2], slug=slug,
                                parent=Category.objects.get(name=row[1]))

                    if elId == 3 and el != '':
                        try:
                            slug = slugify(row[2] + " " + row[3])
                            category_path += "/"
                            category_path += slug
                            category = Category.objects.get(
                                name=row[3], parent=Category.objects.get(name=row[2]))
                            print('Kategoria istnieje: ', category)
                        except Category.DoesNotExist:
                            Category.objects.create(
                                name=row[3], slug=slug,
                                parent=Category.objects.get(name=row[2]))

                    if elId == 4 and el != '':
                        try:
                            metadata = {'categoryPath': category_path,
                                        'description': row[5], 'brandDict': row[6]}
                            product_type = ProductType.objects.get(
                                name=row[4], metadata=metadata)
                            print('Typ produktu istnieje: ', product_type)
                        except ProductType.DoesNotExist:
                            product_type = ProductType.objects.create(name=row[4],
                                                                      slug=slugify(
                                                                          row[1] + " " +
                                                                          row[2] + " " +
                                                                          row[4]),
                                                                      has_variants=False,
                                                                      metadata=metadata)

                            brand_attribute = Attribute.objects.get(slug=row[6])

                            AttributeProduct.objects.create(attribute=brand_attribute,
                                                            product_type=product_type)
                            AttributeProduct.objects.create(attribute=color_attribute,
                                                            product_type=product_type)
                            AttributeProduct.objects.create(attribute=size_attribute,
                                                            product_type=product_type)
                            AttributeProduct.objects.create(
                                attribute=material_attribute, product_type=product_type)

                            AttributeProduct.objects.create(
                                attribute=quality_attribute, product_type=product_type)
