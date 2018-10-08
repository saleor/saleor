import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.defaultfilters import slugify
from graphql_jwt.decorators import permission_required

from ....product import models
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...product.types import ProductType
from ..types import Attribute, AttributeTypeEnum, AttributeValue


class AttributeCreateValueInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description='Name displayed in the interface.')
    value = graphene.String(
        required=True, description='Real value eg. HEX color.')


class AttributeCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description='Name displayed in the interface.')
    values = graphene.List(
        AttributeCreateValueInput,
        description='Attribute values to be created for this attribute.')


class AttributeMixin:
    @classmethod
    def clean_attribute_value_uniqueness(cls, values, errors, error_msg):
        """Checks if all provided values are unique."""
        if len(set(values)) != len(values):
            cls.add_error(errors, cls.ATTRIBUTE_VALUES_FIELD, error_msg)
        return errors

    @classmethod
    def clean_attribute_values(cls, values, errors):
        """Validates if a valid AttributeValue instance can be created using
        the data provided.
        """
        for value_data in values:
            value_data['slug'] = slugify(value_data['name'])
            attribute_value = models.AttributeValue(**value_data)
            try:
                attribute_value.full_clean()
            except ValidationError as validation_errors:
                for field in validation_errors.message_dict:
                    if field == 'attribute':
                        continue
                    for message in validation_errors.message_dict[field]:
                        error_field = '%(values_field)s:%(field)s' % {
                            'values_field': cls.ATTRIBUTE_VALUES_FIELD,
                            'field': field}
                        cls.add_error(errors, error_field, message)
        return errors

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        slug = slugify(cleaned_input['name'])
        cleaned_input['slug'] = slug

        # Slugs are created automatically from the names, but those should be
        # unique.
        attribute_with_same_slug_exists = instance._meta.model.objects.filter(
            slug=slug).exclude(pk=getattr(instance, 'pk', None)).exists()
        if attribute_with_same_slug_exists:
            cls.add_error(errors, 'name', 'Attribute\'s name is not unique.')

        values = cleaned_input.get(cls.ATTRIBUTE_VALUES_FIELD)
        if not values:
            return cleaned_input

        # All provided names should be unique to each other
        cls.clean_attribute_value_uniqueness(
            [v['name'] for v in values], errors,
            'Duplicated AttributeValue names provided.')

        slugs = []
        for value in values:
            value['slug'] = slugify(value['name'])
            slugs.append(value['slug'])
        # All provided names should resolve to unique slugs
        cls.clean_attribute_value_uniqueness(
            slugs, errors, 'Provided AttributeValue names are not unique.')

        cls.clean_attribute_values(values, errors)
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        values = cleaned_data.get(cls.ATTRIBUTE_VALUES_FIELD) or []
        for value in values:
            instance.values.create(**value)


class AttributeCreate(AttributeMixin, ModelMutation):
    ATTRIBUTE_VALUES_FIELD = 'values'

    attribute = graphene.Field(
        Attribute, description='A created Attribute.')

    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of the ProductType to create an attribute for.')
        type = AttributeTypeEnum(
            required=True,
            description=(
                'Type of an Attribute, if should be created for Products'
                ' or Variants of this ProductType.'))
        input = AttributeCreateInput(
            required=True,
            description='Fields required to create an attribute.')

    class Meta:
        description = 'Creates an attribute.'
        model = models.Attribute

    @classmethod
    def clean_product_type_variant_attributes(
            cls, product_type, type, errors):
        if (
            type == AttributeTypeEnum.VARIANT.name
                and not product_type.has_variants):
            cls.add_error(
                errors, 'product_type',
                'Cannot create an Attribute for ProductType'
                'not supporting ProductVariants.')
        return errors

    @classmethod
    @permission_required('product.manage_products')
    def mutate(cls, root, info, id, type, input):
        errors = []
        product_type = cls.get_node_or_error(
            info, id, errors, 'id', ProductType)
        if not product_type:
            return AttributeCreate(errors=errors)

        instance = models.Attribute()
        cleaned_input = cls.clean_input(info, instance, input, errors)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        cls.clean_product_type_variant_attributes(
            product_type, type, errors)
        if errors:
            return cls(errors=errors)

        instance.save()
        if type == AttributeTypeEnum.VARIANT.name:
            product_type.variant_attributes.add(instance)
        else:
            product_type.product_attributes.add(instance)
        cls._save_m2m(info, instance, cleaned_input)
        return cls.success_response(instance)


class AttributeUpdateInput(graphene.InputObjectType):
    name = graphene.String(
        description='Name displayed in the interface.')
    remove_values = graphene.List(
        graphene.ID, name='removeValues', required=True,
        description='List of attributes to be removed from this attribute.')
    add_values = graphene.List(
        AttributeCreateValueInput, name='addValues', required=True,
        description='Attribute values to be created for this attribute.')


class AttributeUpdate(AttributeMixin, ModelMutation):
    ATTRIBUTE_VALUES_FIELD = 'add_values'

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute to update.')
        input = AttributeUpdateInput(
            required=True,
            description='Fields required to update an attribute.')

    class Meta:
        description = 'Updates attribute.'
        model = models.Attribute

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')

    @classmethod
    def clean_remove_values(cls, cleaned_input, instance, errors):
        """Check if AttributeValues to be removed are assigned to given
        Attribute.
        """
        remove_values = cleaned_input.get('remove_values', [])
        if not remove_values:
            return []

        attribute_values = cls.get_nodes_or_error(
            ids=remove_values, errors=errors,
            only_type=AttributeValue, field=cls.ATTRIBUTE_VALUES_FIELD)
        if attribute_values:
            for value in attribute_values:
                if value.attribute != instance:
                    cls.add_error(
                        errors, 'remove_values:%s' % value,
                        'AttributeValue does not belong to this Attribute.')
        return attribute_values

    @classmethod
    def clean_add_values(cls, cleaned_input, instance, errors):
        """Check if AttributeValue with the same slug or name already exists.
        """
        existing_attribute_values = instance.values.values_list('slug', 'name')
        existing_slugs, existing_names = zip(*existing_attribute_values)
        for value in cleaned_input.get('add_values', []):
            if value['name'] in existing_names:
                cls.add_error(
                    errors, 'add_values:%s' % value['name'],
                    'AttributeValue with given name already exists.')
            if value['slug'] in existing_slugs:
                cls.add_error(
                    errors, 'add_values:%s' % value['slug'],
                    'AttributeValue name is not unique.')
        return errors

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        cleaned_input['remove_values'] = cls.clean_remove_values(
            cleaned_input, instance, errors)
        cls.clean_add_values(cleaned_input, instance, errors)
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        for attribute_value in cleaned_data.get('remove_values', []):
            attribute_value.delete()


class AttributeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute to delete.')

    class Meta:
        description = 'Deletes an attribute.'
        model = models.Attribute

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')


class AttributeValueCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description='Name displayed in the interface.')
    value = graphene.String(
        required=True, description='Real value eg. HEX color.')


class AttributeValueCreate(BaseMutation):
    attribute = graphene.Field(
        Attribute, description='A related Attribute.')
    attribute_value = graphene.Field(
        AttributeValue, description='Created AttributeValue.')

    class Arguments:
        id = graphene.ID(
            required=True, name='attribute',
            description='Attribute to which value will be assigned.')
        input = AttributeValueCreateInput(
            required=True,
            description='Fields required to create an AttributeValue.')

    class Meta:
        description = 'Creates an AttributeValue.'

    @classmethod
    def clean_input(
            cls, name, slug, errors, attribute, attribute_value_pk=None):
        other_values = attribute.values.exclude(pk=attribute_value_pk)
        duplicated_values_exists = other_values.filter(
            Q(name=name) | Q(slug=slug)).exists()
        if duplicated_values_exists:
            cls.add_error(errors, 'name', 'Provided name is not unique.')
        return errors

    @classmethod
    @permission_required('product.manage_products')
    def mutate(cls, root, info, id, input):
        errors = []
        attribute = cls.get_node_or_error(info, id, errors, 'id', Attribute)
        if not attribute:
            return AttributeValueCreate(errors=errors)

        name = input['name']
        slug = slugify(name)
        cls.clean_input(name, slug, errors, attribute, attribute_value_pk=None)
        if errors:
            return AttributeValueCreate(errors=errors)

        attribute_value = attribute.values.create(
            name=name, value=input['value'], slug=slug)
        return AttributeValueCreate(
            attribute=attribute, attribute_value=attribute_value)


class AttributeValueUpdate(AttributeValueCreate):
    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of an AttributeValue to update.')
        input = AttributeValueCreateInput(
            required=True,
            description='Fields required to update an AttributeValue.')

    class Meta:
        description = 'Updates an AttributeValue.'

    @classmethod
    @permission_required('product.manage_products')
    def mutate(cls, root, info, id, input):
        errors = []
        attribute_value = cls.get_node_or_error(
            info, id, errors, 'id', AttributeValue)
        if not attribute_value:
            return AttributeValueUpdate(errors=errors)

        attribute = attribute_value.attribute
        name = input['name']
        slug = slugify(name)
        cls.clean_input(
            name, slug, errors, attribute,
            attribute_value_pk=attribute_value.pk)
        if errors:
            return AttributeValueUpdate(errors=errors)

        attribute_value.name = name
        attribute_value.value = input['value']
        attribute_value.slug = slug
        attribute_value.save(update_fields=['slug', 'name', 'value'])
        return AttributeValueUpdate(
            attribute=attribute, attribute_value=attribute_value)


class AttributeValueDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of an AttributeValue to delete.')

    class Meta:
        description = 'Deletes an AttributeValue.'
        model = models.AttributeValue

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')
