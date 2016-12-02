from __future__ import unicode_literals

from django.core.management import CommandError, BaseCommand

from ...feeds import SaleorGoogleMerchant
from ... import utils


class Command(BaseCommand):
    help = ('Updates integration feeds.'
            'If feed name not provided, updates all available feeds')
    feed_classes = {'saleor': SaleorGoogleMerchant}

    def add_arguments(self, parser):
        parser.add_argument('feed_name', nargs='*', type=str, default=None)

    def handle(self, *args, **options):
        feed_names = options.get('feed_name') or self.feed_classes.keys()
        for feed_name in feed_names:
            feed = self.feed_classes.get(feed_name)
            if feed is None:
                raise CommandError('Feed "%s" does not exist' % feed_name)
            utils.update_feed(feed())
