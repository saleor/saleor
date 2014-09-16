import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'saleor.settings')

import sys
import faker
import unicodedata
from django.contrib.auth.hashers import make_password
from saleor.userprofile.models import User, Address, AddressBook

factory = faker.Factory.create('pl_PL')


def create_fake_user():
    first_name = factory.first_name()
    last_name = factory.last_name()

    _first = unicodedata.normalize('NFD', first_name).encode('ascii', 'ignore')
    _last = unicodedata.normalize('NFD', last_name).encode('ascii', 'ignore')

    email = u'%s.%s@example.com' % (_first.lower(), _last.lower())

    user = User.objects.create(
        email=email,
        password=make_password('password'))
    user.save()
    print email

    address = Address.objects.create(
        first_name=first_name,
        last_name=last_name,
        street_address_1=factory.street_address(),
        city=factory.city(),
        postal_code=factory.postcode(),
        country='PL')

    addr_book = AddressBook.objects.create(
        user=user,
        address=address)
    addr_book.save()

    user.address_book.add(addr_book)
    user.default_billing_address = addr_book
    user.is_active = True
    user.save()


if __name__ == '__main__':
    try:
        count = int(sys.argv[1])
    except:
        count = 10
    for _ in range(count):
        create_fake_user()
