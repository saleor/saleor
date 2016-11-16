from __future__ import unicode_literals

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from django.core.files.storage import default_storage
from django.core.management import CommandError, BaseCommand

from saleor.integrations.feeds import SaleorFeed


class Command(BaseCommand):
    help = 'Updates integration feeds. '
    feed_classes = {'saleor': SaleorFeed}

    def add_arguments(self, parser):
        parser.add_argument('feed_name', nargs='+', type=str)

    @staticmethod
    def get_feed_content(feed, url_name=''):
        feed = feed.get_feed()
        buffer = StringIO()
        feed.write(buffer, 'utf-8')
        return buffer.getvalue()

    @staticmethod
    def save_feed(file_path, content):
        with default_storage.open(file_path, 'w') as output_file:
            output_file.write(content)

    def update_feed(self, feed):
        content = self.get_feed_content(feed, feed.url)
        self.save_feed(feed.file_path, content)

    def handle(self, *args, **options):
        feed_names = options['feed_name'] or self.feed_classes.keys()
        for feed_name in feed_names:
            feed = self.feed_classes.get(feed_name)
            if feed is None:
                raise CommandError('Feed "%s" does not exist' % feed_name)
            self.update_feed(feed())
