import gzip
import csv

from django.core.files.storage import default_storage


def update_feed(feed):
    with default_storage.open(feed.file_path, 'w') as output_file:
        output_compressed = gzip.GzipFile(fileobj=output_file)
        writer = csv.DictWriter(output_compressed,feed.attributes,
                                delimiter=str("\t"))
        writer.writeheader()
        for item in feed.items():
            writer.writerow(feed.item_attributes(item))
        output_compressed.close()
