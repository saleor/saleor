from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Order
import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_API_KEY


class OrderTests(APITestCase):
    def setUp(self):
        # Create a real PaymentIntent using Stripe API
        self.payment_intent = stripe.PaymentIntent.create(
            amount=10000,
            currency='usd',
            payment_method_types=['card'],
            description='Test PaymentIntent for Order',
        )
        
        stripe.PaymentIntent.confirm(
            self.payment_intent['id'],
            payment_method='pm_card_visa'
        )
        
        self.order = Order.objects.create(
            customer_name='Test Customer',
            total=100.00,
            status='pending',
            payment_intent_id=self.payment_intent['id']
        )
    def test_create_payment_intent(self):
        url = reverse('order-pay', kwargs={'pk': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('client_secret', response.data)

    def test_print_receipt(self):
        url = reverse('order-print-receipt', kwargs={'pk': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'Receipt printed')

    def test_reprint_receipt(self):
        url = reverse('order-reprint-receipt', kwargs={'pk': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'Receipt reprinted')

    def test_cancel_order(self):
        url = reverse('order-cancel', kwargs={'pk': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'Order cancelled')

    def test_refund_order(self):
        url = reverse('order-refund', kwargs={'pk': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'Order refunded')
