import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy
from django.views.decorators.http import require_POST

from . import utils
from ..core.utils import get_paginator_items
from ..product.models import Product, ProductVariant
from .models import Wishlist, WishlistItem


@login_required
def user_wishlist(request):
    # type: (HttpRequest) -> django.http.HttpResponse
    """
    Get or create user wishlist and redirect into public view list.
    """
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return redirect('wishlist:public-wishlist', token=wishlist.token)


def public_wishlist(request, token):
    # type: (HttpRequest, str) -> HttpResponse
    """
    View with items added to wishlist. If wishlist is private, only it's owner
    can see this page.
    """
    wishlist_query = Wishlist.objects.all().filter(Q(user__pk=request.user.pk)|
                                                   Q(public=True))
    wishlist = get_object_or_404(wishlist_query, token=token)
    items = WishlistItem.objects.all().filter(
        wishlist=wishlist).select_related(
        'product__product_class').prefetch_related(
        'variant_object__stock', 'product__images',
        'product__product_class__variant_attributes__values')
    items_page = get_paginator_items(
        items, settings.PAGINATE_BY, request.GET.get('page'))
    items = utils.wishlist_items_with_availability(
        items_page, discounts=request.discounts,
        local_currency=request.currency)
    ctx = {'wishlist': wishlist, 'items': items, 'items_page': items_page}

    return TemplateResponse(request, 'wishlist/list.html', ctx)


@require_POST
@login_required
def add_wishlist_item(request):
    # type: (HttpRequest) -> JsonResponse
    """
    Ajax view used for adding items to logged in user wishlist.
    """
    variant_pk = request.POST.get('variant')
    if variant_pk:
        variant = get_object_or_404(ProductVariant, pk=variant_pk)
        added = utils.add_variant_to_user_wishlist(request.user, variant)
    else:
        attributes = json.loads(request.POST.get('attributes', "{}"))
        product = get_object_or_404(Product, pk=request.POST.get('product'))
        added = utils.add_to_user_wishlist(request.user, product, attributes)
    if added:
        messages.success(request, pgettext_lazy('wishlist', 'New item added into list'))
        return JsonResponse(status=201, data={})
    messages.info(request, pgettext_lazy('wishlist', 'Item already in wishlist'))
    return JsonResponse(data={})


@login_required
def delete_wishlist_item(request, item_pk):
    # type: (HttpRequest, str) -> HttpResponse
    """
    View used for removing items from user wishlist.
    """
    item = get_object_or_404(WishlistItem.objects.filter(
        wishlist__user=request.user), pk=item_pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, pgettext_lazy('wishlist', 'Item removed from list'))
        return redirect('wishlist:user-wishlist')
    ctx = {'item': item,
           'item_name': '%s - %s' % (item.product,
                                     utils.wishlist_item_variant_name(item))}
    return TemplateResponse(
        request, 'wishlist/modal_delete.html', ctx)
