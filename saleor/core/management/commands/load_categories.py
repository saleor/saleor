import csv

from django.core.management.base import BaseCommand

from saleor.product.models import Category, ProductType
from django.utils.text import slugify


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='category file path')

    def handle(self, *args, **options):

        self.load_categories(options['path'])

    def load_categories(self, path):
        with open(path, encoding="utf8", errors='ignore') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for rid, row in enumerate(reader):
                for elId, el in enumerate(row):
                    if(elId == 0 and el != ''):

                        try:
                            category = Category.objects.get(name=row[0])
                            print('Kategoria istnieje: ', category)
                        except Category.DoesNotExist:
                            Category.objects.create(name=row[0], slug=slugify(row[0]))

                    if(elId == 1 and el != ''):

                        try:
                            category = Category.objects.get(name=row[1], parent=Category.objects.get(name=row[0]))
                            print('Kategoria istnieje: ', category)
                        except Category.DoesNotExist:
                            Category.objects.create(name=row[1], slug=slugify(row[0] + " " + row[1]), parent=Category.objects.get(name=row[0]))

                    if (elId == 2 and el != ''):
                        try:
                            category = Category.objects.get(name=row[2], parent=Category.objects.get(name=row[1]))
                            print('Kategoria istnieje: ', category)
                        except Category.DoesNotExist:
                            Category.objects.create(name=row[2], slug=slugify(row[1] + " " + row[2]), parent=Category.objects.get(name=row[1]))

                    if (elId == 3 and el != ''):
                        try:
                            category = Category.objects.get(name=row[3], parent=Category.objects.get(name=row[2]))
                            print('Kategoria istnieje: ', category)
                        except Category.DoesNotExist:
                            Category.objects.create(name=row[3], slug=slugify(row[2] + " " + row[3]), parent=Category.objects.get(name=row[2]))

