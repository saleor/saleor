import json

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy
from impersonate.views import impersonate as orig_impersonate
from random import randint

from ..account.models import User
from ..dashboard.views import staff_member_required
from ..product.models import Category
from ..product.utils import products_for_homepage
from ..product.utils.availability import products_with_availability
from ..seo.schema.webpage import get_webpage_schema


def home(request):
    products = products_for_homepage(
        request.user,
        request.site.settings.homepage_collection)[:8]
    products = list(products_with_availability(
        products, discounts=request.discounts, taxes=request.taxes,
        local_currency=request.currency))
    webpage_schema = get_webpage_schema(request)

    # DEMO: get Shop Now links based on current categories, instead of
    # hardcoding them in template.
    num = 3
    shop_now_links = []
    categories = list(Category.objects.all()[:num])
    for dummy in range(num):
        if categories:
            category = categories.pop()
            link = category.get_absolute_url()
        else:
            link = ''
        shop_now_links.append(link)

    return TemplateResponse(
        request, 'home.html', {
            'parent': None,
            'products': products,
            'shop_now_links' : shop_now_links,
            'webpage_schema': json.dumps(webpage_schema)})


@staff_member_required
def styleguide(request):
    return TemplateResponse(request, 'styleguide.html')


def impersonate(request, uid):
    response = orig_impersonate(request, uid)
    if request.session.modified:
        msg = pgettext_lazy(
            'Impersonation message',
            'You are now logged as {}'.format(User.objects.get(pk=uid)))
        messages.success(request, msg)
    return response


def handle_404(request, exception=None):
    ctx = {'variant': randint(0, 2)}
    return TemplateResponse(request, '404.html', ctx, status=404)


def manifest(request):
    return TemplateResponse(
        request, 'manifest.json', content_type='application/json')


def privacy_policy(request):
    return TemplateResponse(request, 'privacy_policy.html')
