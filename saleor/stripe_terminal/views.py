from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import requests
from rest_framework.views import APIView
from django.conf import settings
import stripe
import pdfkit
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.views import APIView
from .models import Order

stripe.api_key = settings.STRIPE_API_KEY
pdfkit_config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
SALEOR_API_URL = settings.SALEOR_API_URL
API_TOKEN = settings.API_TOKEN


class FetchVariantsView(APIView):
    def get(self, request, *args, **kwargs):
        query = """
        query {
          products(first: 10, channel: "default-channel") {
            edges {
              node {
                id
                name
                variants {
                  id
                  name
                }
              }
            }
          }
        }
        """
        
        headers = {
            "Authorization": f"Bearer {settings.API_TOKEN}"
        }
        
        response = requests.post(
            settings.SALEOR_API_URL,
            json={'query': query},
            headers=headers
        )
        response_data = response.json()
        
        if 'errors' in response_data:
            return Response({'errors': response_data['errors']}, status=status.HTTP_400_BAD_REQUEST)
        
        products = response_data.get('data', {}).get('products', {}).get('edges', [])
        variants = []
        
        for product in products:
            product_node = product.get('node', {})
            for variant in product_node.get('variants', []):
                variants.append({
                    'product_name': product_node.get('name'),
                    'variant_id': variant.get('id'),
                    'variant_name': variant.get('name')
                })
        
        return Response({'variants': variants}, status=status.HTTP_200_OK)

class CheckoutViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def create_checkout(self, request):
        data = request.data
        mutation = """
        mutation CreateCheckout($input: CheckoutCreateInput!) {
          checkoutCreate(input: $input) {
            checkout {
              id
              token
            }
            errors {
              field
              message
            }
          }
        }
        """
        variables = {
            "input": {
                "email": data['email'],
                "lines": data['lines'],
                "shippingAddress": {
                    "firstName": data['shipping_address']['firstName'],
                    "lastName": data['shipping_address']['lastName'],
                    "streetAddress1": data['shipping_address']['streetAddress1'],
                    "streetAddress2": data['shipping_address']['streetAddress2'],
                    "city": data['shipping_address']['city'],
                    "postalCode": data['shipping_address']['postalCode'],
                    "country": data['shipping_address']['country'],
                    "countryArea": data['shipping_address']['countryArea']
                },
                "billingAddress": {
                    "firstName": data['billing_address']['firstName'],
                    "lastName": data['billing_address']['lastName'],
                    "streetAddress1": data['billing_address']['streetAddress1'],
                    "streetAddress2": data['billing_address']['streetAddress2'],
                    "city": data['billing_address']['city'],
                    "postalCode": data['billing_address']['postalCode'],
                    "country": data['billing_address']['country'],
                    "countryArea": data['shipping_address']['countryArea']
                },
                "channel": data['channel']
            }
        }
        
        headers = {
            "Authorization": f"Bearer {settings.API_TOKEN}"
        }
        response = requests.post(
            settings.SALEOR_API_URL,
            json={'query': mutation, 'variables': variables},
            headers=headers
        )
        
        response_data = response.json()
        if 'errors' in response_data:
            return Response({'error': response_data['errors']}, status=status.HTTP_400_BAD_REQUEST)
        
        data = response_data.get('data', {}).get('checkoutCreate', {})
        if data.get('errors'):
            return Response({'errors': data['errors']}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'checkout': data['checkout']}, status=status.HTTP_201_CREATED)
    

class OrderCreateFromCheckoutViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def create_order(self, request):
        checkout_id = request.data.get('checkout_id')
        if not checkout_id:
            return Response({'error': 'Checkout ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch available shipping methods
        query = """
        query {
          checkout(id: "%s") {
            availableShippingMethods {
              id
              name
            }
          }
        }
        """ % checkout_id
        
        headers = {
            "Authorization": f"Bearer {settings.API_TOKEN}"
        }
        
        response = requests.post(
            settings.SALEOR_API_URL,
            json={'query': query},
            headers=headers
        )
        
        if response.status_code != 200:
            return Response({'error': f"Failed to fetch shipping methods, status code: {response.status_code}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            shipping_methods = response.json()['data']['checkout']['availableShippingMethods']
        except (KeyError, requests.exceptions.JSONDecodeError):
            return Response({'error': 'Failed to fetch available shipping methods'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not shipping_methods:
            return Response({'error': 'No shipping methods available'}, status=status.HTTP_400_BAD_REQUEST)
        
        shipping_method_id = shipping_methods[0]['id']
        
        # Set the shipping method for the checkout
        mutation = """
        mutation {
          checkoutShippingMethodUpdate(checkoutId: "%s", shippingMethodId: "%s") {
            checkout {
              id
              shippingMethod {
                id
                name
              }
            }
            errors {
              field
              message
            }
          }
        }
        """ % (checkout_id, shipping_method_id)
        
        response = requests.post(
            settings.SALEOR_API_URL,
            json={'query': mutation},
            headers=headers
        )
        
        if response.status_code != 200:
            return Response({'error': f"Failed to set shipping method, status code: {response.status_code}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError as e:
            return Response({'error': 'Failed to decode JSON response from Saleor API'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if 'errors' in response_data:
            return Response({'error': response_data['errors']}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create order from checkout
        mutation = """
        mutation CreateOrderFromCheckout($checkoutId: ID!) {
          orderCreateFromCheckout(id: $checkoutId) {
            order {
              id
              status
            }
            errors {
              field
              message
            }
          }
        }
        """
        
        variables = {
            "checkoutId": checkout_id
        }
        
        response = requests.post(
            settings.SALEOR_API_URL,
            json={'query': mutation, 'variables': variables},
            headers=headers
        )
        
        if response.status_code != 200:
            return Response({'error': f"Failed to reach Saleor API, status code: {response.status_code}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError as e:
            return Response({'error': 'Failed to decode JSON response from Saleor API'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if 'errors' in response_data:
            return Response({'error': response_data['errors']}, status=status.HTTP_400_BAD_REQUEST)
        
        data = response_data.get('data', {}).get('orderCreateFromCheckout', {})
        if data.get('errors'):
            return Response({'errors': data['errors']}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'order': data['order']}, status=status.HTTP_201_CREATED)
    

class OrderViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
      saleor_order_id = request.data.get('saleor_order_id')
      if not saleor_order_id:
          return Response({'error': 'Saleor order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
      
      query = """
      query {
        order(id: "%s") {
          id
          created
          status
          total {
            gross {
              amount
              currency
            }
          }
          user {
            email
          }
          shippingAddress {
            firstName
            lastName
            streetAddress1
            streetAddress2
            city
            postalCode
            country {
              code
            }
          }
          lines {
            productName
            variantName
            quantity
            unitPrice {
              gross {
                amount
                currency
              }
            }
          }
          paymentStatus
          shippingMethod {
            name
          }
        }
      }
      """ % saleor_order_id

      headers = {
          "Authorization": f"Bearer {settings.API_TOKEN}"
      }
      
      response = requests.post(
          settings.SALEOR_API_URL,
          json={'query': query},
          headers=headers
      )

      if response.status_code != 200:
          return Response({'error': f"Failed to fetch order details, status code: {response.status_code}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
      try:
          order_data = response.json()['data']['order']
      except (KeyError, requests.exceptions.JSONDecodeError):
          return Response({'error': 'Failed to fetch order details'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
      total_amount = int(order_data['total']['gross']['amount'] * 100)
      shipping_address = order_data['shippingAddress']
      # customer_email = order_data['user']['email']
      
      try:
          intent = stripe.PaymentIntent.create(
              amount=total_amount,
              currency=order_data['total']['gross']['currency'].lower(),
              payment_method_types=['card'],
              description=f"Order #{order_data['id']}",
              metadata={'order_id': str(order_data['id'])},
              # receipt_email=customer_email,
              shipping={
                  'name': f"{shipping_address['firstName']} {shipping_address['lastName']}",
                  'address': {
                      'line1': shipping_address['streetAddress1'],
                      'line2': shipping_address['streetAddress2'],
                      'city': shipping_address['city'],
                      'postal_code': shipping_address['postalCode'],
                      'country': shipping_address['country']['code']
                  },
              }
          )
          test_payment_method = 'pm_card_visa'

          intent = stripe.PaymentIntent.confirm(
              intent['id'],
              payment_method=test_payment_method
          )

          if intent['status'] == 'requires_capture':
              intent = stripe.PaymentIntent.capture(intent['id'])

          if intent['status'] == 'succeeded':
              order_status = 'paid'
          else:
              order_status = 'payment_failed'

          order = Order.objects.create(order_id=saleor_order_id, payment_intent_id=intent['id'])
          return Response({'client_secret': intent['client_secret'], 'status': f"{order_status} with id {order.payment_intent_id}"}, status=status.HTTP_200_OK)
      
      except stripe.error.InvalidRequestError as e:
        return Response({'error': f"Error processing payment: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'])
    def print_receipt(self, request):
        saleor_order_id = request.query_params.get('saleor_order_id')
        if not saleor_order_id:
            return Response({'error': 'Saleor order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
      
        query = """
        query {
          order(id: "%s") {
            id
            created
            status
            total {
              gross {
                amount
                currency
              }
            }
            user {
              email
            }
            shippingAddress {
              firstName
              lastName
              streetAddress1
              streetAddress2
              city
              postalCode
              country {
                code
              }
            }
            lines {
              productName
              variantName
              quantity
              unitPrice {
                gross {
                  amount
                  currency
                }
              }
            }
            paymentStatus
            shippingMethod {
              name
            }
          }
        }
        """ % saleor_order_id

        headers = {
            "Authorization": f"Bearer {settings.API_TOKEN}"
        }
        
        response = requests.post(
            settings.SALEOR_API_URL,
            json={'query': query},
            headers=headers
        )

        if response.status_code != 200:
            return Response({'error': f"Failed to fetch order details, status code: {response.status_code}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            order_data = response.json()['data']['order']
        except (KeyError, requests.exceptions.JSONDecodeError):
            return Response({'error': 'Failed to fetch order details'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        receipt_html = render_to_string('admin/stripe_terminal/order/receipt.html', {'order': order_data})
        pdf = pdfkit.from_string(receipt_html, False, configuration=pdfkit_config)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{order_data["id"]}.pdf"'
        return Response({'status': 'Receipt printed'}, status=status.HTTP_200_OK)

    
    @action(detail=False, methods=['get'])
    def reprint_receipt(self, request):
        saleor_order_id = request.query_params.get('saleor_order_id')
        if not saleor_order_id:
            return Response({'error': 'Saleor order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
      
        query = """
        query {
          order(id: "%s") {
            id
            created
            status
            total {
              gross {
                amount
                currency
              }
            }
            user {
              email
            }
            shippingAddress {
              firstName
              lastName
              streetAddress1
              streetAddress2
              city
              postalCode
              country {
                code
              }
            }
            lines {
              productName
              variantName
              quantity
              unitPrice {
                gross {
                  amount
                  currency
                }
              }
            }
            paymentStatus
            shippingMethod {
              name
            }
          }
        }
        """ % saleor_order_id

        headers = {
            "Authorization": f"Bearer {settings.API_TOKEN}"
        }
        
        response = requests.post(
            settings.SALEOR_API_URL,
            json={'query': query},
            headers=headers
        )

        if response.status_code != 200:
            return Response({'error': f"Failed to fetch order details, status code: {response.status_code}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            order_data = response.json()['data']['order']
        except (KeyError, requests.exceptions.JSONDecodeError):
            return Response({'error': 'Failed to fetch order details'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        receipt_html = render_to_string('admin/stripe_terminal/order/receipt.html', {'order': order_data})
        pdf = pdfkit.from_string(receipt_html, False, configuration=pdfkit_config)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{order_data["id"]}.pdf"'
        return Response({'status': 'Receipt reprinted'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancel_order(self, request):
        saleor_order_id = request.data.get('saleor_order_id')
        if not saleor_order_id:
            return Response({'error': 'Saleor order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
      
        mutation = """
        mutation {
          orderCancel(id: "%s") {
            order {
              id
              status
            }
            errors {
              field
              message
            }
          }
        }
        """ % saleor_order_id

        headers = {
            "Authorization": f"Bearer {settings.API_TOKEN}"
        }

        response = requests.post(
            settings.SALEOR_API_URL,
            json={'query': mutation},
            headers=headers
        )

        if response.status_code != 200:
            return Response({'error': f"Failed to cancel order, status code: {response.status_code}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = response.json()
        if 'errors' in response_data:
            return Response({'error': response_data['errors']}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'Order cancelled'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def refund_order(self, request):
      saleor_order_id = request.data.get('saleor_order_id')
      if not saleor_order_id:
          return Response({'error': 'Saleor order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
      
      try:
          order = Order.objects.last()
      except Order.DoesNotExist:
          return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

      payment_intent_id = order.payment_intent_id

      if not payment_intent_id:
          return Response({'error': 'No payment intent ID found for this order'}, status=status.HTTP_400_BAD_REQUEST)

      try:
          payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
          if payment_intent.status in ['succeeded', 'requires_capture']:
              refund = stripe.Refund.create(
                  payment_intent=payment_intent.id,
                  amount=payment_intent.amount  # Refund full amount
              )
              return Response({'status': 'Order refunded', 'refund': refund}, status=status.HTTP_200_OK)
          else:
              return Response({'error': 'PaymentIntent for this order has not been successfully captured or charged.'}, status=status.HTTP_400_BAD_REQUEST)
      except stripe.error.InvalidRequestError as e:
          return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'])
    def view_in_stripe_dashboard(self, request):
      saleor_order_id = request.query_params.get("saleor_order_id")
      if not saleor_order_id:
          return Response({'error': 'Saleor order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
      
      try:
          order = Order.objects.filter(order_id=saleor_order_id).last()
      except Order.DoesNotExist:
          return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
      
      payment_intent_id = order.payment_intent_id

      if not payment_intent_id:
          return Response({'error': 'No payment intent ID found for this order'}, status=status.HTTP_400_BAD_REQUEST)

      dashboard_url = f"{settings.STRIPE_PAYMENT_URL}{payment_intent_id}"
      return Response({'url': dashboard_url}, status=status.HTTP_200_OK)


