from .forms import ProductForm
from .models import Product
from django.http import HttpResponsePermanentRedirect, Http404
from django.template.response import TemplateResponse


def index(request):
    products = Product.objects.all()

    return TemplateResponse(request, 'product/index.html', {
        'products': products
    })


def details(request, slug, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Http404()
    if product.get_slug() != slug:
        return HttpResponsePermanentRedirect(product.get_absolute_url())
    form = ProductForm(request.POST or None, cart=request.cart,
                       product=product)
    if form.is_valid():
        form.save()
    return TemplateResponse(request, 'product/details.html', {
        'product': product,
        'form': form
    })
