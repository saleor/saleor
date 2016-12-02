from __future__ import unicode_literals

import gzip
import csv

from django.core.files.storage import default_storage


def update_feed(feed):
    with default_storage.open(feed.file_path, 'wb') as output_file:
        if feed.compression:
            try:
                output = gzip.open(output_file, 'wt')
            except TypeError:
                output = gzip.GzipFile(fileobj=output_file, mode='w')
        else:
            output = output_file

        writer = csv.DictWriter(output, feed.attributes,
                                dialect=csv.excel_tab)
        writer.writeheader()
        for item in feed.items():
            writer.writerow(feed.item_attributes(item))

        if feed.compression:
            output.close()
