from __future__ import unicode_literals

from django.core.management import CommandError, BaseCommand

from saleor.integrations.feeds import SaleorFeed
from saleor.integrations import utils


class Command(BaseCommand):
    help = 'Updates integration feeds. '
    feed_classes = {'saleor': SaleorFeed}

    def add_arguments(self, parser):
        parser.add_argument('feed_name', nargs='+', type=str)

    def handle(self, *args, **options):
        feed_names = options['feed_name'] or self.feed_classes.keys()
        for feed_name in feed_names:
            feed = self.feed_classes.get(feed_name)
            if feed is None:
                raise CommandError('Feed "%s" does not exist' % feed_name)
            utils.update_feed(feed())
