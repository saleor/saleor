from . import get_cart_from_request
from .forms import ReplaceCartLineFormSet
from django.template.response import TemplateResponse

def index(request):
    cart = get_cart_from_request(request)

    formset = ReplaceCartLineFormSet(request.POST or None, cart=cart)

    if formset.is_valid():
        formset.save()

    return TemplateResponse(request, 'cart/index.html', {
        'cart': cart,
        'formset': formset
    })
