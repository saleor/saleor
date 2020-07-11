import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from saleor.product.models import Attribute, AttributeValue


class Command(BaseCommand):
    version = "1.0"

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='category file path')

    def handle(self, *args, **options):

        self.load_attriubtes(options['path'])

    @staticmethod
    def load_attriubtes(path):
        with open(path, encoding="utf8", errors='ignore') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for rid, row in enumerate(reader):
                attribute: Attribute
                for elId, el in enumerate(row):

                    if elId == 0 and el != '':

                        try:
                            attribute = Attribute.objects.get(name=row[0])
                            print('Atrybut istnieje: ', attribute)
                        except Attribute.DoesNotExist:
                            attribute = Attribute.objects.create(name=row[0],
                                                                 slug=row[1])

                    if elId == 2 and el != '':

                        try:
                            slug = slugify(row[2].replace('ł', 'l').replace('Ł', 'L'))
                            attribute_value = AttributeValue.objects.get(slug=slug,
                                                                         name=row[2],
                                                                         attribute=attribute)
                            print('Wartość istnieje: ', attribute_value)
                        except AttributeValue.DoesNotExist:
                            AttributeValue.objects.create(name=row[2],
                                                          slug=slug,
                                                          attribute=attribute,
                                                          value=row[3])
