from rest_framework import serializers
from ..order.models import Order, Payment, OrderedItem
from ..userprofile.models import Address


class AddressSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    address1 = serializers.CharField(source='street_address_1')
    address2 = serializers.CharField(source='street_address_2')
    zipcode = serializers.CharField(source='postal_code')
    state = serializers.CharField(source='country_area')

    class Meta:
        model = Address
        fields = ('firstname', 'lastname', 'address1', 'address2',
                  'city', 'zipcode', 'state', 'country', 'phone')


class PaymentsSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk')
    amount = serializers.DecimalField(source='total', max_digits=9,
                                      decimal_places=2, default='0.0')
    payment_method = serializers.CharField(source='variant')

    class Meta:
        model = Payment
        fields = ('id', 'amount', 'payment_method', 'status')


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
        fields = ('product_id', 'name', 'price', 'quantity')


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
            'value': order.get_total().tax
        }]

    def get_channel(self, order):
        return 'Saleor'

    class Meta:
        model = Order
        fields = (
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
            'payments'
        )
