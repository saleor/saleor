from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from .forms import ProductForm
from .models import Product, Category


def product_details(request, slug, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.get_slug() != slug:
        return HttpResponsePermanentRedirect(product.get_absolute_url())
    form = ProductForm(cart=request.cart, product=product,
                       data=request.POST or None)
    if form.is_valid():
        form.save()
    return TemplateResponse(request, 'product/details.html', {
        'product': product,
        'form': form
    })


def category_index(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.all()
    return TemplateResponse(request, 'category/index.html', {
        'products': products,
        'category': category
    })
