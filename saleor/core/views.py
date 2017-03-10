from django.template.response import TemplateResponse

from ..core.utils import get_user_shipping_country
from ..product.utils import products_with_availability, products_for_homepage
from ..cart.forms import CountryForm


def home(request):
    products = products_for_homepage()[:8]
    products = products_with_availability(
        products, discounts=request.discounts, local_currency=request.currency)
    return TemplateResponse(
        request, 'home.html',
        {'products': products, 'parent': None})

def styleguide(request):
    default_country = get_user_shipping_country(request)
    country_form = CountryForm(initial={'country': default_country})
    return TemplateResponse(
        request, 'styleguide.html',
        {'country_form': country_form})
