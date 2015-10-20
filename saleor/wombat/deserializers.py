from rest_framework import serializers
from .fields import PriceField
from ..product.models import Product, ProductImage


class ProductImageDeserializer(serializers.Serializer):
    url = serializers.URLField()
    position = serializers.IntegerField()
    title = serializers.CharField()
    type = serializers.CharField()

    def create(self, validated_data):
        return ProductImage.objects.create(
            product=self.context['product'],
            order=validated_data['position'],
            image=validated_data['url'],
            alt=validated_data['title']
        )


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

    def create(self, validated_data):
        product_data = {
            'name': validated_data['name'],
            'description': validated_data['description'],
            'price': validated_data['price'],
            'available_on': validated_data['available_on'],
            'weight': '1'
        }
        product = Product.objects.create(**product_data)
        images = ProductImageDeserializer(data=validated_data['images'],
                                          context={'product': product},
                                          many=True)
        if images.is_valid():
            images.save()
        return product

    def update(self, instance, validated_data):
        pass
