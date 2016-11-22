import gzip
import csv

from django.core.files.storage import default_storage


def update_feed(feed):
    with default_storage.open(feed.file_path, 'w') as output_file:
        if feed.compression:
            output = gzip.GzipFile(fileobj=output_file)
        else:
            output = output_file

        writer = csv.DictWriter(output,feed.attributes,
                                delimiter=str("\t"))
        writer.writeheader()
        for item in feed.items():
            writer.writerow(feed.item_attributes(item))

        if feed.compression:
            output.close()
