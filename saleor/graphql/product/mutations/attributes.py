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
        description='''Value different than a textual name e.g. color
        in a hexadecimal format.''')


class AttributeCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description='Name displayed in the interface.')
    values = graphene.List(
        AttributeCreateValueInput,
        description='Attribute values to be created for this attribute.')


class AttributeMixin:
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
    def clean_attribute_uniqueness(
            cls, instance, input, errors, product_type=None):
        # Slugs are created automatically from the names, but should be unique
        # within a product type.
        slug = input.get('slug')
        if not product_type:
            product_type = instance.product_type
        query = models.Attribute.objects.filter(slug=slug).filter(
            Q(product_type=product_type)
            | Q(product_variant_type=product_type))
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists():
            msg = (
                'Attribute already exists within product type %s.' %
                product_type)
            cls.add_error(errors, 'name', msg)

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        if 'name' in cleaned_input:
            slug = slugify(cleaned_input['name'])
        elif instance.pk:
            slug = instance.slug
        else:
            cls.add_error(errors, 'name', 'This field cannot be blank.')
            return cleaned_input
        cleaned_input['slug'] = slug

        values = cleaned_input.get(cls.ATTRIBUTE_VALUES_FIELD)
        if not values:
            return cleaned_input

        slugs = []
        for value in values:
            value['slug'] = slugify(value['name'])
            slugs.append(value['slug'])
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
    product_type = graphene.Field(
        ProductType,
        description='A product type to which an attribute was added.')

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
    def clean_attribute_value_uniqueness(cls, values, errors, error_msg):
        """Checks if all provided values are unique."""
        if len(set(values)) != len(values):
            cls.add_error(errors, cls.ATTRIBUTE_VALUES_FIELD, error_msg)
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

        # This check happens here as we need product_type and we cannot get it
        # in clean_input.
        cls.clean_attribute_uniqueness(
            instance, cleaned_input, errors, product_type=product_type)

        # Check if unique values were provided
        values = cleaned_input.get(cls.ATTRIBUTE_VALUES_FIELD)
        slugs = []
        for value in values:
            value['slug'] = slugify(value['name'])
            slugs.append(value['slug'])
        cls.clean_attribute_value_uniqueness(
            slugs, errors, 'Provided AttributeValue names are not unique.')

        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        if errors:
            return AttributeCreate(errors=errors)

        instance.save()
        if type == AttributeTypeEnum.VARIANT.name:
            product_type.variant_attributes.add(instance)
        else:
            product_type.product_attributes.add(instance)
        cls._save_m2m(info, instance, cleaned_input)
        return AttributeCreate(
            attribute=instance, product_type=product_type, errors=errors)


class AttributeUpdateInput(graphene.InputObjectType):
    name = graphene.String(
        description='Name displayed in the interface.')
    remove_values = graphene.List(
        graphene.ID, name='removeValues',
        description='List of attributes to be removed from this attribute.')
    add_values = graphene.List(
        AttributeCreateValueInput, name='addValues',
        description='Attribute values to be created for this attribute.')


class AttributeUpdate(AttributeMixin, ModelMutation):
    ATTRIBUTE_VALUES_FIELD = 'add_values'

    product_type = graphene.Field(
        ProductType, description='A related product type.')

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
    def clean_remove_values(cls, cleaned_input, instance, errors):
        """Check if AttributeValues to be removed are assigned to given
        Attribute.
        """
        remove_values = cleaned_input.get('remove_values', [])
        if remove_values:
            for value in remove_values:
                if value.attribute != instance:
                    cls.add_error(
                        errors, 'remove_values:%s' % value,
                        'AttributeValue does not belong to this Attribute.')
        return remove_values

    @classmethod
    def clean_add_values(cls, cleaned_input, instance, errors):
        """Check if AttributeValue with the same slug or name already exists.
        """
        existing_values = instance.values.values_list('slug', 'name')
        if existing_values:
            existing_slugs, existing_names = zip(*existing_values)
            for value in cleaned_input.get('add_values', []):
                already_exists = (
                    value['name'] in existing_names or
                    value['slug'] in existing_slugs)
                if already_exists:
                    cls.add_error(
                        errors, 'add_values:%s' % value['name'],
                        'Value with given name already exists.')
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

    @classmethod
    @permission_required('product.manage_products')
    def mutate(cls, root, info, id, input):
        errors = []
        instance = cls.get_node_or_error(info, id, errors, 'id', Attribute)
        cleaned_input = cls.clean_input(info, instance, input, errors)
        product_type = instance.product_type

        cls.clean_attribute_uniqueness(
            instance, cleaned_input, errors, product_type=product_type)

        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        if errors:
            return AttributeUpdate(errors=errors)

        instance.save()
        cls._save_m2m(info, instance, cleaned_input)
        return AttributeUpdate(
            attribute=instance, product_type=product_type, errors=errors)


class AttributeDelete(ModelDeleteMutation):
    product_type = graphene.Field(
        ProductType, description='A related product type.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute to delete.')

    class Meta:
        description = 'Deletes an attribute.'
        model = models.Attribute

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.product_type = (
            instance.product_type or instance.product_variant_type)
        return response


class AttributeValueCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description='Name displayed in the interface.')
    value = graphene.String(description='Real value eg. HEX color.')


class AttributeValueCreate(ModelMutation):
    attribute = graphene.Field(Attribute, description='A related Attribute.')

    class Arguments:
        id = graphene.ID(
            required=True, name='attribute',
            description='Attribute to which value will be assigned.')
        input = AttributeValueCreateInput(
            required=True,
            description='Fields required to create an AttributeValue.')

    class Meta:
        description = 'Creates a value for an attribute.'
        model = models.AttributeValue

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        cleaned_input['slug'] = slugify(cleaned_input['name'])

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response


class AttributeValueUpdate(AttributeValueCreate):
    attribute = graphene.Field(Attribute, description='A related Attribute.')

    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of an AttributeValue to update.')
        input = AttributeValueCreateInput(
            required=True,
            description='Fields required to update an AttributeValue.')

    class Meta:
        description = 'Updates value of an attribute.'
        model = models.AttributeValue

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        if 'name' in cleaned_input:
            cleaned_input['slug'] = slugify(cleaned_input['name'])


class AttributeValueDelete(ModelDeleteMutation):
    attribute = graphene.Field(Attribute, description='A related Attribute.')

    class Arguments:
        id = graphene.ID(required=True, description='ID of a value to delete.')

    class Meta:
        description = 'Deletes a value of an attribute.'
        model = models.AttributeValue

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response
