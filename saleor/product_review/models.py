from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from saleor.product.models import Product


class ProductReview(models.Model):
    product = models.ForeignKey(Product,related_name='products',on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    score = models.FloatField(
        default=settings.PRODUCT_REVIEW_MIN_SCORE,
        validators=[MinValueValidator(settings.PRODUCT_REVIEW_MIN_SCORE),MaxValueValidator(settings.PRODUCT_REVIEW_MAX_SCORE)]
    )
    review = models.TextField()
    updated_on = models.DateTimeField(auto_now=True)

    def clean(self):
        previous_reviews_count = self.__class__.objects.filter(user=self.user,product=self.product).count()
        if previous_reviews_count >= settings.MAX_REVIEW_PER_USER:
            raise ValidationError('Maximum possible reviews already given',code='max_reviews')
