from __future__ import absolute_import, unicode_literals

from ..index import FilterField, RelatedFields, SearchField

from .elasticsearch import (
    ElasticsearchIndex, ElasticsearchMapping, ElasticsearchSearchBackend, ElasticsearchSearchQuery,
    ElasticsearchSearchResults)


def get_model_root(model):
    """
    This function finds the root model for any given model. The root model is
    the highest concrete model that it descends from. If the model doesn't
    descend from another concrete model then the model is it's own root model so
    it is returned.

    Examples:
    >>> get_model_root(wagtailcore.Page)
    wagtailcore.Page

    >>> get_model_root(myapp.HomePage)
    wagtailcore.Page

    >>> get_model_root(wagtailimages.Image)
    wagtailimages.Image
    """
    if model._meta.parents:
        parent_model = list(model._meta.parents.items())[0][0]
        return get_model_root(parent_model)

    return model


class Elasticsearch2Mapping(ElasticsearchMapping):
    edgengram_analyzer_config = {
        'analyzer': 'edgengram_analyzer',
        'search_analyzer': 'standard',
    }

    def get_field_column_name(self, field):
        # Fields in derived models get prefixed with their model name, fields
        # in the root model don't get prefixed at all
        # This is to prevent mapping clashes in cases where two page types have
        # a field with the same name but a different type.
        root_model = get_model_root(self.model)
        definition_model = field.get_definition_model(self.model)

        if definition_model != root_model:
            prefix = definition_model._meta.app_label.lower() + '_' + definition_model.__name__.lower() + '__'
        else:
            prefix = ''

        if isinstance(field, FilterField):
            return prefix + field.get_attname(self.model) + '_filter'
        elif isinstance(field, SearchField):
            return prefix + field.get_attname(self.model)
        elif isinstance(field, RelatedFields):
            return prefix + field.field_name

    def get_content_type(self):
        """
        Returns the content type as a string for the model.

        For example: "wagtailcore.Page"
                     "myapp.MyModel"
        """
        return self.model._meta.app_label + '.' + self.model.__name__

    def get_all_content_types(self):
        """
        Returns all the content type strings that apply to this model.
        This includes the models' content type and all concrete ancestor
        models that inherit from Indexed.

        For example: ["myapp.MyPageModel", "wagtailcore.Page"]
                     ["myapp.MyModel"]
        """
        # Add our content type
        content_types = [self.get_content_type()]

        # Add all ancestor classes content types as well
        ancestor = self.get_parent()
        while ancestor:
            content_types.append(ancestor.get_content_type())
            ancestor = ancestor.get_parent()

        return content_types

    def get_document(self, obj):
        # In the Elasticsearch 2 backend, we use a more efficient way to
        # represent the content type of a document.

        # Instead of using a long string of model names that is queried using a
        # "prefix" query, we instead use a multi-value string field and query it
        # using a simple "match" query.

        # The only reason why this isn't implemented in the Elasticsearch 1.x
        # backend yet is backwards compatibility
        doc = super(Elasticsearch2Mapping, self).get_document(obj)
        doc['content_type'] = self.get_all_content_types()
        return doc


class Elasticsearch2Index(ElasticsearchIndex):
    def add_model(self, model):
        # Get mapping
        mapping = self.mapping_class(model)

        # Put mapping
        self.es.indices.put_mapping(
            # pass update_all_types=True as a workaround to avoid "Can't redefine search field" errors -
            # see https://github.com/torchbox/wagtail/issues/2968
            index=self.name, doc_type=mapping.get_document_type(), body=mapping.get_mapping(),
            update_all_types=True
        )


class Elasticsearch2SearchQuery(ElasticsearchSearchQuery):
    mapping_class = Elasticsearch2Mapping

    def get_content_type_filter(self):
        # Query content_type using a "match" query. See comment in
        # Elasticsearch2Mapping.get_document for more details
        content_type = self.mapping_class(self.queryset.model).get_content_type()

        return {
            'match': {
                'content_type': content_type
            }
        }


class Elasticsearch2SearchResults(ElasticsearchSearchResults):
    pass


class Elasticsearch2SearchBackend(ElasticsearchSearchBackend):
    mapping_class = Elasticsearch2Mapping
    index_class = Elasticsearch2Index
    query_class = Elasticsearch2SearchQuery
    results_class = Elasticsearch2SearchResults

    def get_index_for_model(self, model):
        # Split models up into separate indices based on their root model.
        # For example, all page-derived models get put together in one index,
        # while images and documents each have their own index.
        root_model = get_model_root(model)
        index_suffix = '__' + root_model._meta.app_label.lower() + '_' + root_model.__name__.lower()

        return self.index_class(self, self.index_name + index_suffix)


SearchBackend = Elasticsearch2SearchBackend
