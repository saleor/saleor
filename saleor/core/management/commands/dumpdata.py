from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.dumpdata import sort_dependencies
from django.core import serializers
from django.db import router, DEFAULT_DB_ALIAS
from django.db.models.query import QuerySet
from django.utils.datastructures import SortedDict

from optparse import make_option


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--format', default='json', dest='format',
            help='Specifies the output serialization format for fixtures.'),
        make_option(
            '--indent', default=None, dest='indent', type='int',
            help=('Specifies the indent level to use when pretty-printing'
                  ' output')),
        make_option(
            '--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS,
            help=('Nominates a specific database to dump fixtures from.'
                  ' Defaults to the "default" database.')),
        make_option(
            '-e', '--exclude', dest='exclude', action='append', default=[],
            help=('An appname or appname.ModelName to exclude (use multiple'
                  ' --exclude to exclude multiple apps/models).')),
        make_option(
            '-n', '--natural', action='store_true', dest='use_natural_keys',
            default=False, help='Use natural keys if they are available.'),
        make_option(
            '-a', '--all', action='store_true', dest='use_base_manager',
            default=False,
            help=("Use Django's base manager to dump all models stored in the"
                  " database, including those that would otherwise be filtered"
                  " or modified by a custom manager.")),
        make_option(
            '--pks', dest='primary_keys',
            help=("Only dump objects with "
                  "given primary keys. Accepts a comma seperated list of keys."
                  " This option will only work when you specify one model."))
    )
    help = ("Output the contents of the database as a fixture of the given "
            "format (using each model's default manager unless --all is "
            "specified).")
    args = '[appname appname.ModelName ...]'

    def handle(self, *app_labels, **options):
        from django.db.models import get_app, get_apps, get_model

        format = options.get('format')
        indent = options.get('indent')
        using = options.get('database')
        excludes = options.get('exclude')
        show_traceback = options.get('traceback')
        use_natural_keys = options.get('use_natural_keys')
        use_base_manager = options.get('use_base_manager')
        pks = options.get('primary_keys')

        if pks:
            primary_keys = pks.split(',')
        else:
            primary_keys = []

        excluded_apps = set()
        excluded_models = set()
        for exclude in excludes:
            if '.' in exclude:
                app_label, model_name = exclude.split('.', 1)
                model_obj = get_model(app_label, model_name)
                if not model_obj:
                    raise CommandError(
                        'Unknown model in excludes: %s' % (exclude,))
                excluded_models.add(model_obj)
            else:
                try:
                    app_obj = get_app(exclude)
                    excluded_apps.add(app_obj)
                except ImproperlyConfigured:
                    raise CommandError('Unknown app in excludes: %s' % exclude)

        if len(app_labels) == 0:
            if primary_keys:
                raise CommandError(
                    "You can only use --pks option with one model")
            app_list = SortedDict((app, None) for app in get_apps()
                                  if app not in excluded_apps)
        else:
            if len(app_labels) > 1 and primary_keys:
                raise CommandError(
                    "You can only use --pks option with one model")
            app_list = SortedDict()
            for label in app_labels:
                try:
                    app_label, model_label = label.split('.')
                    try:
                        app = get_app(app_label)
                    except ImproperlyConfigured:
                        raise CommandError(
                            "Unknown application: %s" % (app_label,))
                    if app in excluded_apps:
                        continue
                    model = get_model(app_label, model_label)
                    if model is None:
                        raise CommandError(
                            "Unknown model: %s.%s" % (app_label, model_label))

                    if app in app_list.keys():
                        if app_list[app] and model not in app_list[app]:
                            app_list[app].append(model)
                    else:
                        app_list[app] = [model]
                except ValueError:
                    if primary_keys:
                        raise CommandError(
                            "You can only use --pks option with one model")
                    # This is just an app - no model qualifier
                    app_label = label
                    try:
                        app = get_app(app_label)
                    except ImproperlyConfigured:
                        raise CommandError(
                            "Unknown application: %s" % (app_label,))
                    if app in excluded_apps:
                        continue
                    app_list[app] = None

        # Check that the serialization format exists; this is a shortcut to
        # avoid collating all the objects and _then_ failing.
        if format not in serializers.get_public_serializer_formats():
            try:
                serializers.get_serializer(format)
            except serializers.SerializerDoesNotExist:
                pass

            raise CommandError("Unknown serialization format: %s" % format)

        def get_objects():
            # Collate the objects to be serialized.
            for model in sort_dependencies(app_list.items()):
                if model in excluded_models:
                    continue
                if not model._meta.proxy and router.allow_syncdb(using, model):
                    if use_base_manager:
                        objects = model._base_manager
                    else:
                        objects = QuerySet(model).all()

                    queryset = objects.using(using).order_by(
                        model._meta.pk.name)
                    if primary_keys:
                        queryset = queryset.filter(pk__in=primary_keys)
                    for obj in queryset.iterator():
                        yield obj

        try:
            self.stdout.ending = None
            serializers.serialize(
                format, get_objects(), indent=indent,
                use_natural_keys=use_natural_keys, stream=self.stdout)
        except Exception as e:
            if show_traceback:
                raise
            raise CommandError("Unable to serialize database: %s" % e)
