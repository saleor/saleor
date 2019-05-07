import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.defaultfilters import slugify

from ....product import models
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ...product.types import ProductType
from ..descriptions import AttributeDescriptions, AttributeValueDescriptions
from ..enums import AttributeTypeEnum
from ..types import Attribute


class AttributeValueCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description=AttributeValueDescriptions.NAME)
    value = graphene.String(description=AttributeValueDescriptions.VALUE)


class AttributeCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description=AttributeDescriptions.NAME)
    values = graphene.List(
        AttributeValueCreateInput, description=AttributeDescriptions.VALUES)


class AttributeUpdateInput(graphene.InputObjectType):
    name = graphene.String(description=AttributeDescriptions.NAME)
    remove_values = graphene.List(
        graphene.ID, name='removeValues',
        description='IDs of values to be removed from this attribute.')
    add_values = graphene.List(
        AttributeValueCreateInput, name='addValues',
        description='New values to be created for this attribute.')


class AttributeMixin:

    @classmethod
    def check_unique_values(cls, values_input, attribute):
        # Check values uniqueness in case of creating new attribute.
        existing_values = attribute.values.values_list('slug', flat=True)
        for value_data in values_input:
            slug = slugify(value_data['name'])
            if slug in existing_values:
                msg = (
                    'Value %s already exists within this attribute.' %
                    value_data['name'])
                raise ValidationError({cls.ATTRIBUTE_VALUES_FIELD: msg})

        new_slugs = [
            slugify(value_data['name']) for value_data in values_input]
        if len(set(new_slugs)) != len(new_slugs):
            raise ValidationError({
                cls.ATTRIBUTE_VALUES_FIELD:
                'Provided values are not unique.'})

    @classmethod
    def clean_values(cls, cleaned_input, attribute):
        """Clean attribute values.

        Transforms AttributeValueCreateInput into AttributeValue instances.
        Slugs are created from given names and checked for uniqueness within
        an attribute.
        """
        values_input = cleaned_input[cls.ATTRIBUTE_VALUES_FIELD]
        for value_data in values_input:
            value_data['slug'] = slugify(value_data['name'])
            attribute_value = models.AttributeValue(
                **value_data, attribute=attribute)
            try:
                attribute_value.full_clean()
            except ValidationError as validation_errors:
                for field in validation_errors.message_dict:
                    if field == 'attribute':
                        continue
                    for msg in validation_errors.message_dict[field]:
                        raise ValidationError({
                            cls.ATTRIBUTE_VALUES_FIELD: msg})
        cls.check_unique_values(values_input, attribute)

    @classmethod
    def clean_attribute(
            cls, instance, cleaned_input, product_type=None):
        if 'name' in cleaned_input:
            slug = slugify(cleaned_input['name'])
        elif instance.pk:
            slug = instance.slug
        else:
            raise ValidationError({'name': 'This field cannot be blank.'})
        cleaned_input['slug'] = slug

        if not product_type:
            product_type = instance.product_type

        query = models.Attribute.objects.filter(slug=slug).filter(
            Q(product_type=product_type)
            | Q(product_variant_type=product_type))
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists():
            raise ValidationError({
                'name': 'Attribute already exists within this product type.'})
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, attribute, cleaned_data):
        super()._save_m2m(info, attribute, cleaned_data)
        values = cleaned_data.get(cls.ATTRIBUTE_VALUES_FIELD) or []
        for value in values:
            attribute.values.create(**value)


class AttributeCreate(AttributeMixin, ModelMutation):
    ATTRIBUTE_VALUES_FIELD = 'values'

    attribute = graphene.Field(Attribute, description='A created Attribute.')
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
                'Type of an Attribute, if should be created for Products '
                'or Variants of this ProductType.'))
        input = AttributeCreateInput(
            required=True,
            description='Fields required to create an attribute.')

    class Meta:
        description = 'Creates an attribute.'
        model = models.Attribute
        permissions = ('product.manage_products', )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        product_type = cls.get_node_or_error(
            info, data.get('id'), only_type=ProductType)
        instance = models.Attribute()

        cleaned_input = cls.clean_input(info, instance, data.get('input'))
        cls.clean_attribute(
            instance, cleaned_input, product_type=product_type)
        cls.clean_values(cleaned_input, instance)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance)

        instance.save()
        if data.get('type') == AttributeTypeEnum.VARIANT.name:
            product_type.variant_attributes.add(instance)
        else:
            product_type.product_attributes.add(instance)
        cls._save_m2m(info, instance, cleaned_input)
        return AttributeCreate(attribute=instance, product_type=product_type)


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
        permissions = ('product.manage_products', )

    @classmethod
    def clean_remove_values(cls, cleaned_input, instance):
        """Check if AttributeValues to be removed are assigned to given
        Attribute.
        """
        remove_values = cleaned_input.get('remove_values', [])
        for value in remove_values:
            if value.attribute != instance:
                msg = 'Value %s does not belong to this attribute.' % value
                raise ValidationError({'remove_values': msg})
        return remove_values

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        for attribute_value in cleaned_data.get('remove_values', []):
            attribute_value.delete()

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        instance = cls.get_node_or_error(info, id, only_type=Attribute)

        cleaned_input = cls.clean_input(info, instance, input)
        product_type = instance.product_type
        cls.clean_attribute(
            instance, cleaned_input, product_type=product_type)
        cls.clean_values(cleaned_input, instance)
        cls.clean_remove_values(cleaned_input, instance)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance)

        instance.save()
        cls._save_m2m(info, instance, cleaned_input)
        return AttributeUpdate(
            attribute=instance, product_type=product_type)


class AttributeDelete(ModelDeleteMutation):
    product_type = graphene.Field(
        ProductType, description='A related product type.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute to delete.')

    class Meta:
        description = 'Deletes an attribute.'
        model = models.Attribute
        permissions = ('product.manage_products', )

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.product_type = (
            instance.product_type or instance.product_variant_type)
        return response


class AttributeValueCreate(ModelMutation):
    attribute = graphene.Field(Attribute, description='A related Attribute.')

    class Arguments:
        attribute_id = graphene.ID(
            required=True, name='attribute',
            description='Attribute to which value will be assigned.')
        input = AttributeValueCreateInput(
            required=True,
            description='Fields required to create an AttributeValue.')

    class Meta:
        description = 'Creates a value for an attribute.'
        model = models.AttributeValue
        permissions = ('product.manage_products', )

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        cleaned_input['slug'] = slugify(cleaned_input['name'])
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info, attribute_id, input):
        attribute = cls.get_node_or_error(
            info, attribute_id, only_type=Attribute)

        instance = models.AttributeValue(attribute=attribute)
        cleaned_input = cls.clean_input(info, instance, input)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance)

        instance.save()
        cls._save_m2m(info, instance, cleaned_input)
        return AttributeValueCreate(
            attribute=attribute, attributeValue=instance)


class AttributeValueUpdate(ModelMutation):
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
        permissions = ('product.manage_products', )

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        if 'name' in cleaned_input:
            cleaned_input['slug'] = slugify(cleaned_input['name'])
        return cleaned_input

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response


class AttributeValueDelete(ModelDeleteMutation):
    attribute = graphene.Field(Attribute, description='A related Attribute.')

    class Arguments:
        id = graphene.ID(required=True, description='ID of a value to delete.')

    class Meta:
        description = 'Deletes a value of an attribute.'
        model = models.AttributeValue
        permissions = ('product.manage_products', )

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response
