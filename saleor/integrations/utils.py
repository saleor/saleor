try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from django.core.files.storage import default_storage


def get_feed_content(feed, url_name=''):
    feed = feed.get_feed()
    buffer = StringIO()
    feed.write(buffer, 'utf-8')
    return buffer.getvalue()


def save_feed(file_path, content):
    with default_storage.open(file_path, 'w') as output_file:
        output_file.write(content)


def update_feed(feed):
    content = get_feed_content(feed, feed.url)
    save_feed(feed.file_path, content)
