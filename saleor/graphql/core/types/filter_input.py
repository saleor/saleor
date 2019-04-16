import six
from graphene import InputField, InputObjectType
from graphene.types.inputobjecttype import InputObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs
from graphene_django.filter.utils import get_filterset_class

from .converter import convert_form_field


class FilterInputObjectType(InputObjectType):
    """Class for storing and serving django-filtres as graphQL input.
    FilterSet class which inherits from django-filters.FilterSet should be
    provided with using fitlerset_class argument."""
    @classmethod
    def __init_subclass_with_meta__(
            cls, _meta=None, model=None, filterset_class=None,
            fields=None, **options):
        cls.custom_filterset_class = filterset_class
        cls.filterset_class = None
        cls.fields = fields
        cls.model = model

        if not _meta:
            _meta = InputObjectTypeOptions(cls)

        fields = cls.get_filtering_args_from_filterset()
        fields = yank_fields_from_attrs(fields, _as=InputField)
        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields

        super().__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def get_filtering_args_from_filterset(cls):
        """ Inspect a FilterSet and produce the arguments to pass to
            a Graphene Field. These arguments will be available to
            filter against in the GraphQL
        """
        if not cls.custom_filterset_class:
            assert cls.model and cls.fields, (
                'Provide filterset class or model and fields requested to '
                'create default filterset')

        meta = dict(model=cls.model, fields=cls.fields)
        cls.filterset_class = get_filterset_class(
            cls.custom_filterset_class, **meta
        )

        args = {}
        for name, filter_field in six.iteritems(
                cls.filterset_class.base_filters):
            input_class = getattr(filter_field, 'input_class', None)
            if input_class:
                field_type = convert_form_field(filter_field)
            else:
                field_type = convert_form_field(filter_field.field)
                field_type.description = filter_field.label
            kwargs = getattr(field_type, 'kwargs', {})
            field_type.kwargs = kwargs
            args[name] = field_type
        return args
