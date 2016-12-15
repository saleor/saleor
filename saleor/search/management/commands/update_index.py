from __future__ import absolute_import, unicode_literals

import collections

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from ...backends import get_search_backend
from ...index import get_indexed_models


def group_models_by_index(backend, models):
    """
    This takes a search backend and a list of models. By calling the
    get_index_for_model method on the search backend, it groups the models into
    the indices that they will be indexed into.

    It returns an ordered mapping of indices to lists of models within each
    index.

    For example, Elasticsearch 2 requires all page models to be together, but
    separate from other content types (eg, images and documents) to prevent
    field mapping collisions (eg, images and documents):

    >>> group_models_by_index(elasticsearch2_backend, [
    ...     wagtailcore.Page,
    ...     myapp.HomePage,
    ...     myapp.StandardPage,
    ...     wagtailimages.Image
    ... ])
    {
        <Index wagtailcore_page>: [wagtailcore.Page, myapp.HomePage, myapp.StandardPage],
        <Index wagtailimages_image>: [wagtailimages.Image],
    }
    """
    indices = {}
    models_by_index = collections.OrderedDict()

    for model in models:
        index = backend.get_index_for_model(model)

        if index:
            indices.setdefault(index.name, index)
            models_by_index.setdefault(index.name, [])
            models_by_index[index.name].append(model)

    return collections.OrderedDict([
        (indices[index_name], index_models)
        for index_name, index_models in models_by_index.items()
    ])


class Command(BaseCommand):
    def update_backend(self, backend_name, schema_only=False):
        self.stdout.write("Updating backend: " + backend_name)

        backend = get_search_backend(backend_name)

        if not backend.rebuilder_class:
            self.stdout.write("Backend '%s' doesn't require rebuilding" % backend_name)
            return

        models_grouped_by_index = group_models_by_index(backend, get_indexed_models()).items()
        if not models_grouped_by_index:
            self.stdout.write(backend_name + ": No indices to rebuild")

        for index, models in models_grouped_by_index:
            self.stdout.write(backend_name + ": Rebuilding index %s" % index.name)

            # Start rebuild
            rebuilder = backend.rebuilder_class(index)
            index = rebuilder.start()

            # Add models
            for model in models:
                index.add_model(model)

            # Add objects
            object_count = 0
            if not schema_only:
                for model in models:
                    self.stdout.write('{}: {}.{} '.format(backend_name, model._meta.app_label, model.__name__).ljust(35), ending='')

                    # Add items (1000 at a time)
                    for chunk in self.print_iter_progress(self.queryset_chunks(model.get_indexed_objects())):
                        index.add_items(model, chunk)
                        object_count += len(chunk)

                    self.print_newline()

            # Finish rebuild
            rebuilder.finish()

            self.stdout.write(backend_name + ": indexed %d objects" % object_count)
            self.print_newline()

    def add_arguments(self, parser):
        parser.add_argument(
            '--backend', action='store', dest='backend_name', default=None,
            help="Specify a backend to update")
        parser.add_argument(
            '--schema-only', action='store_true', dest='schema_only', default=False,
            help="Prevents loading any data into the index")

    def handle(self, **options):
        # Get list of backends to index
        if options['backend_name']:
            # index only the passed backend
            backend_names = [options['backend_name']]
        elif hasattr(settings, 'SEARCH_BACKENDS'):
            # index all backends listed in settings
            backend_names = settings.SEARCH_BACKENDS.keys()
        else:
            # index the 'default' backend only
            backend_names = ['default']

        # Update backends
        for backend_name in backend_names:
            self.update_backend(backend_name, schema_only=options['schema_only'])

    def print_newline(self):
        self.stdout.write('')

    def print_iter_progress(self, iterable):
        """
        Print a progress meter while iterating over an iterable. Use it as part
        of a ``for`` loop::

            for item in self.print_iter_progress(big_long_list):
                self.do_expensive_computation(item)

        A ``.`` character is printed for every value in the iterable,
        a space every 10 items, and a new line every 50 items.
        """
        for i, value in enumerate(iterable, start=1):
            yield value
            self.stdout.write('.', ending='')
            if i % 40 == 0:
                self.print_newline()
                self.stdout.write(' ' * 35, ending='')

            elif i % 10 == 0:
                self.stdout.write(' ', ending='')

            self.stdout.flush()

    # Atomic so the count of models doesnt change as it is iterated
    @transaction.atomic
    def queryset_chunks(self, qs, chunk_size=1000):
        """
        Yield a queryset in chunks of at most ``chunk_size``. The chunk yielded
        will be a list, not a queryset. Iterating over the chunks is done in a
        transaction so that the order and count of items in the queryset
        remains stable.
        """
        i = 0
        while True:
            items = list(qs[i * chunk_size:][:chunk_size])
            if not items:
                break
            yield items
            i += 1
