from unidecode import unidecode
from django.utils.text import slugify
import os
try:
    import urlparse
except ImportError:
    # Python 3
    from urllib import parse as urlparse

import requests
import tempfile
from django.core.files.storage import default_storage
from django.core.files import File
from rest_framework import serializers
from .fields import PriceField
from ..product.models import (Product, ProductImage, Category, ProductAttribute,
                              ProductVariant, Stock)


def download_image(image_url):
    temp = tempfile.mktemp()
    content = requests.get(image_url, stream=True)
    with open(temp, 'wb') as f:
        for chunk in content.iter_content():
            if chunk:
                f.write(chunk)
    file_name = ''.join(os.path.splitext(
        os.path.basename(urlparse.urlsplit(image_url).path)))
    new_path = default_storage.save(file_name, File(open(temp)))

    return new_path


class ProductImageDeserializer(serializers.Serializer):
    url = serializers.URLField()
    position = serializers.IntegerField()
    title = serializers.CharField()
    type = serializers.CharField()

    def create(self, validated_data):
        image_path = download_image(validated_data['url'])
        return ProductImage.objects.create(
            product=self.context['product'],
            order=validated_data['position'],
            image=image_path,
            alt=validated_data['title']
        )


class VariantsDeserializer(serializers.Serializer):
    sku = serializers.CharField()
    price = PriceField()
    cost_price = PriceField()
    quantity = serializers.IntegerField()
    options = serializers.DictField()
    images = ProductImageDeserializer(many=True)

    def get_attributes(self, attributes_data):
        attr_map = {}
        for attr_name, value in attributes_data.items():
            attr = ProductAttribute.objects.get(name=attr_name)
            attr_map[attr.pk] = value
        return attr_map

    def create(self, validated_data):
        product = self.context['product']
        attributes = self.get_attributes(validated_data['options'])
        variant = ProductVariant.objects.create(
            sku=validated_data['sku'],
            product=product,
            attributes=attributes,
            price_override=validated_data['price']
        )
        stock = Stock.objects.create(
            variant=variant,
            quantity=validated_data['quantity'],
            cost_price=validated_data['cost_price'],
            location='default'
        )
        return variant


class ProductDeserializer(serializers.Serializer):
    name = serializers.CharField()
    sku = serializers.CharField()
    description = serializers.CharField()
    price = PriceField()
    cost_price = PriceField()
    available_on = serializers.DateTimeField(required=False)
    permalink = serializers.CharField()
    meta_description = serializers.CharField(required=False, allow_null=True)
    meta_keywords = serializers.CharField(required=False, allow_null=True)
    shipping_category = serializers.CharField()
    images = ProductImageDeserializer(many=True)
    taxons = serializers.ListField()
    options = serializers.ListField()
    variants = VariantsDeserializer(many=True)

    def create(self, validated_data):
        product = self.save_product(validated_data)
        self.save_images(validated_data, product)
        self.save_categories(validated_data, product)
        self.save_properties(validated_data, product)
        variants = VariantsDeserializer(data=validated_data['variants'],
                                        context={'product': product},
                                        many=True)
        if variants.is_valid():
            variants.save()
        return product

    def save_product(self, validated_data):
        product_data = {
            'name': validated_data['name'],
            'description': validated_data['description'],
            'price': validated_data['price'],
            'available_on': validated_data['available_on'],
            'weight': '1'
        }
        return Product.objects.create(**product_data)

    def save_images(self, validated_data, product):
        images = ProductImageDeserializer(data=validated_data['images'],
                                          context={'product': product},
                                          many=True)
        if images.is_valid():
            images.save()

    def save_categories(self, validated_data, product):
        db_categories = []
        for category_list in validated_data['taxons']:
            parent = None
            for single_category in category_list:
                slug = slugify(unidecode(single_category))
                cat, _ = Category.objects.get_or_create(
                    name=single_category, defaults={'parent': parent,
                                                    'slug': slug})
                parent = cat
                db_categories.append(cat)
        product.categories.add(*db_categories)

    def save_properties(self, validated_data, product):
        attribtues = []
        for product_property in validated_data['options']:
            attr, _ = ProductAttribute.objects.get_or_create(
                name=product_property, display=product_property)
            attribtues.append(attr)
        product.attributes.add(*attribtues)

    def update(self, instance, validated_data):
        pass
