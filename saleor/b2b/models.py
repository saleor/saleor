from saleor import settings
from decimal import Decimal
from functools import partial
from decimal import ROUND_HALF_UP
from prices import Money, fixed_discount, percentage_discount
from django.db import models
from ..account.models import User, PossiblePhoneNumberField, CountryField
from ..discount import DiscountValueType

# Informations about the company
class CompanyInfo(models.Model):
    customer = models.OneToOneField(User, related_name="company", on_delete=models.CASCADE, unique=True, blank=True ,null=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    street_address = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    country = CountryField(null=True, blank=True)
    personal_phone = PossiblePhoneNumberField(max_length=255, null=True, blank=True)
    business_phone = PossiblePhoneNumberField(max_length=255, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)
    uid = models.CharField(max_length=255, null=True, blank=True)
    has_access_to_b2b = models.BooleanField(default=False)
    recieved_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)


class CustomerGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    category_discounts = models.ManyToManyField("CategoryDiscount")
    channel = models.ForeignKey("channel.Channel", related_name="channels", on_delete=models.CASCADE)

#Specific discounts for b2b customers
class CategoryDiscount(models.Model):
    category = models.ForeignKey("product.Category", related_name="category_discounts", blank=True, null=True, on_delete=models.CASCADE)
    value = models.DecimalField(        
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),)
    value_type =  models.CharField(
        max_length=10,
        choices=DiscountValueType.CHOICES,
        default=DiscountValueType.FIXED,
    )


    def get_discount(self, currency):
        if self.value_type == DiscountValueType.FIXED:
            discount_amount = Money(
                self.value, currency
            )
            return partial(fixed_discount, discount=discount_amount)
        if self.value_type == DiscountValueType.PERCENTAGE:
            return partial(
                percentage_discount,
                percentage=self.value,
                rounding=ROUND_HALF_UP,
            )

    def get_discont_amount_for(self, price, currency):
        discount = self.get_discount(currency=currency)
        alter_discount = discount(price)
        if alter_discount.amount < 0:
            return price
        return price - alter_discount
