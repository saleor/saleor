from django.db.models import Q
from rest_framework import serializers
from ..order.models import Order, Payment, OrderedItem, DeliveryGroup
from ..userprofile.models import Address
from ..product.models import Product, ProductVariant, ProductImage, Stock
from .deserializers import ProductDeserializer


class AddressSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    address1 = serializers.CharField(source='street_address_1')
    address2 = serializers.CharField(source='street_address_2')
    zipcode = serializers.CharField(source='postal_code')
    state = serializers.CharField(source='country_area')

    class Meta:
        model = Address
        fields = ['firstname', 'lastname', 'address1', 'address2',
                  'city', 'zipcode', 'state', 'country', 'phone']


class PaymentsSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    amount = serializers.DecimalField(source='total', max_digits=9,
                                      decimal_places=2, default='0.0')
    payment_method = serializers.CharField(source='variant')

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_method', 'status']


class TotalsSerializer(serializers.Serializer):
    item = serializers.DecimalField(max_digits=9, decimal_places=2)
    adjustment = serializers.DecimalField(max_digits=9, decimal_places=2)
    tax = serializers.DecimalField(max_digits=9, decimal_places=2)
    shipping = serializers.DecimalField(max_digits=9, decimal_places=2)
    payment = serializers.DecimalField(max_digits=9, decimal_places=2)
    order = serializers.DecimalField(max_digits=9, decimal_places=2)


class LineItemsSerializer(serializers.ModelSerializer):
    product_id = serializers.CharField()
    name = serializers.CharField(source='product_name')
    price = serializers.DecimalField(source='unit_price_gross', max_digits=9,
                                     decimal_places=2)

    class Meta:
        model = OrderedItem
        fields = ['product_id', 'name', 'price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    billing_address = AddressSerializer()
    shipping_address = AddressSerializer()
    email = serializers.EmailField(source='get_user_email')
    placed_on = serializers.DateTimeField(source='created')
    totals = serializers.SerializerMethodField()
    channel = serializers.SerializerMethodField()
    adjustments = serializers.SerializerMethodField()
    payments = PaymentsSerializer(many=True)
    line_items = LineItemsSerializer(many=True, source='get_items')
    currency = serializers.SerializerMethodField()

    def get_totals(self, order):
        return {
            'item': sum(item.unit_price_gross*item.quantity
                        for item in order.get_items()),
            'adjustment': order.get_total().tax,
            'tax': order.get_total().tax,
            'shipping': order.get_delivery_total().gross,
            'payment': sum(p.total for p in order.payments.all()),
            'order': order.get_total().gross
        }

    def get_adjustments(self, order):
        return [{
            'name': 'Tax',
            'value': order.get_total().tax}]

    def get_channel(self, order):
        return 'Saleor'

    def get_currency(self, order):
        return order.total.currency

    class Meta:
        model = Order
        fields = [
            'id',
            'status',
            'channel',
            'email',
            'currency',
            'placed_on',
            'totals',
            'adjustments',
            'line_items',
            'shipping_address',
            'billing_address',
            'payments']


class ProductVariantSerializer(serializers.ModelSerializer):

    price = serializers.SerializerMethodField()
    cost_price = serializers.DecimalField(max_digits=9, decimal_places=2,
                                          source='get_cost_price')
    quantity = serializers.IntegerField(source='get_stock_quantity')
    options = serializers.SerializerMethodField()

    def get_price(self, obj):
        return obj.get_price().gross

    def get_options(self, obj):
        attributes = obj.product.attributes.all()
        attr_map = {str(a.pk): a.name for a in attributes}
        options = {}
        for attribute_id, value in obj.attributes.items():
            name = attr_map.get(str(attribute_id))
            if name:
                options[name] = value
        return options

    class Meta:
        model = ProductVariant
        fields = ['sku', 'price', 'cost_price', 'options', 'quantity']


class ProductImageSerializer(serializers.ModelSerializer):

    url = serializers.CharField(source='image.url')
    type = serializers.SerializerMethodField()
    dimensions = serializers.SerializerMethodField()
    position = serializers.CharField(source='order')
    title = serializers.CharField(source='alt')

    def get_type(self, obj):
        return 'product_image'

    def get_dimensions(self, obj):
        return {
            'height': obj.image.height,
            'width': obj.image.width
        }

    class Meta:
        model = ProductImage
        fields = ['url', 'position', 'title', 'type', 'dimensions']


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True)
    images = ProductImageSerializer(many=True)
    options = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()
    shipping_category = serializers.SerializerMethodField()
    permalink = serializers.URLField(source='get_absolute_url')

    def get_options(self, product):
        return [a.name for a in product.attributes.all()]

    def get_properties(self, product):
        return {}

    def get_shipping_category(self, product):
        return 'standard'

    class Meta:
        model = Product
        fields = ['id', 'name', 'description',
                  'available_on', 'permalink',
                  # 'meta_description',
                  # 'meta_keywords',
                  'shipping_category', 'options',
                  'properties', 'images', 'variants']

class StockSerializer(serializers.ModelSerializer):
    product_id = serializers.CharField(source='variant.sku')

    class Meta:
        model = Stock
        fields = ['id', 'location', 'quantity', 'product_id']


class BaseWombatGetWebhookSerializer(serializers.Serializer):
    request_id = serializers.CharField(required=True)
    parameters = serializers.DictField(child=serializers.CharField())


class GetWebhookSerializer(BaseWombatGetWebhookSerializer):

    def __init__(self, since_query_field, *args, **kwargs):
        super(GetWebhookSerializer, self).__init__(*args, **kwargs)
        self.since_query_field = since_query_field

    def get_query_filter(self):
        query_filter = Q()
        if self.is_valid():
            parameters = self.data.get('parameters', {})
            since = parameters.get('since')
            pk = parameters.get('id')
            if since:
                query = '%s__gte' % (self.since_query_field, )
                query_filter = Q(**{query: since})
            if pk:
                query_filter = Q(pk=pk)
        return query_filter


class GetInventoryWebhookSerializer(BaseWombatGetWebhookSerializer):

    def get_query_filter(self):
        query_filter = Q()
        if self.is_valid():
            parameters = self.data.get('parameters', {})
            sku = parameters.get('sku')
            if sku:
                query_filter = Q(variant__sku=sku)
        return query_filter


class AddProductWebhookSerializer(serializers.Serializer):
    request_id = serializers.CharField(required=True)
    product = ProductDeserializer()

    def create(self, validated_data):
        product_data = validated_data['product']
        product = ProductDeserializer(data=product_data)
        if product.is_valid():
            product = product.save()
            return product

    def update(self, instance, validated_data):
        product_data = validated_data['product']
        product = ProductDeserializer(instance=instance, data=product_data)
        if product.is_valid():
            return product.save()


class DeliveryGroupSerializer(serializers.ModelSerializer):
    shipping_address = AddressSerializer(source='order.shipping_address')
    tracking = serializers.CharField(source='tracking_number')
    shipped_at = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    email = serializers.EmailField(source='order.get_user_email')
    items = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryGroup
        fields = ['id', 'order', 'email', 'cost', 'status',
                  # 'stock_location',
                  'shipping_method', 'tracking', 'shipped_at',
                  'shipping_address', 'items']

    def get_shipped_at(self, obj):
        pass

    def get_cost(self, obj):
        pass

    def get_items(self, obj):
        return [{
            'name': item.product_name,
            'product_id': item.product_sku,
            'quantity': item.quantity,
            'price': item.unit_price_gross,
            'options': {}
        } for item in obj.items.all()]

