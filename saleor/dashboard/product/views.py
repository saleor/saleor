from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView

from ...product.models import Product, ProductImage, Stock, ProductAttribute, \
    ProductVariant
from ..utils import paginate
from ..views import StaffMemberOnlyMixin, staff_member_required
from . import forms


@staff_member_required
def product_list(request):
    products = Product.objects.prefetch_related('images').select_subclasses()
    form = forms.ProductClassForm(request.POST or None)
    if form.is_valid():
        return redirect('dashboard:product-add')
    products, paginator = paginate(products, 30, request.GET.get('page'))
    ctx = {'form': form,
           'products': products,
           'paginator': paginator}
    return TemplateResponse(request, 'dashboard/product/list.html', ctx)


@staff_member_required
def product_create(request):
    product = Product()
    title = _('Add new product')
    form = forms.ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        product = form.save()
        msg = _('Added product %s') % product
        messages.success(request, msg)
        return redirect('dashboard:product-update', pk=product.pk)
    elif form.errors:
        messages.error(request, _('Your submitted data was not valid - '
                                  'please correct the errors below'))
    ctx = {'product_form': form, 'product': product, 'title': title}
    return TemplateResponse(request, 'dashboard/product/product_form.html', ctx)


@staff_member_required
def product_edit(request, pk):
    product = get_object_or_404(
        Product.objects.select_subclasses().prefetch_related('images',
                                                             'variants'), pk=pk)
    attributes = product.attributes.all()
    images = product.images.all()
    variants = product.variants.select_subclasses()
    stock_items = Stock.objects.filter(variant__in=variants)

    variant_choices = [(variant.pk, variant.name) for variant in variants]
    stock_choices = [(item.pk, item.pk) for item in stock_items]

    form = forms.ProductForm(instance=product)
    variants_delete_form = forms.VariantsBulkDeleteForm(choices=variant_choices)
    stock_delete_form = forms.StockBulkDeleteForm(choices=stock_choices)

    if 'product-form' in request.POST:
        form = forms.ProductForm(request.POST, instance=product)
        product = save_product_form(request, form, False)
        return redirect('dashboard:product-update', pk=product.pk)

    if 'variants-bulk-delete-form' in request.POST:
        variants_delete_form = forms.VariantsBulkDeleteForm(request.POST,
                                                            choices=variant_choices)
        if variants_delete_form.is_valid():
            variants_delete_form.delete()
            success_url = request.POST['success_url']
            return redirect(success_url)

    if 'stock-bulk-delete-form' in request.POST:
        stock_delete_form = forms.StockBulkDeleteForm(request.POST,
                                                      choices=stock_choices)
        if stock_delete_form.is_valid():
            stock_delete_form.delete()
            success_url = request.POST['success_url']
            return redirect(success_url)

    ctx = {'attributes': attributes,
           'images': images, 'product_form': form,
           'product': product,
           'stock_delete_form': stock_delete_form,
           'stock_items': stock_items,
           'title': product.name,
           'variants': variants,
           'variants_delete_form': variants_delete_form}

    if pk:
        images_reorder_url = reverse_lazy('dashboard:product-images-reorder',
                                          kwargs={'product_pk': pk})
        ctx['images_reorder_url'] = images_reorder_url
    return TemplateResponse(request, 'dashboard/product/product_form.html', ctx)


def save_product_form(request, form, creating):
    product = None
    if form.is_valid():
        product = form.save()
        if creating:
            msg = _('Added product %s') % product
        else:
            msg = _('Updated product %s') % product
        messages.success(request, msg)
    else:
        if form.errors:
            messages.error(request, _('Your submitted data was not valid - '
                                      'please correct the errors below'))
    return product


class ProductDeleteView(StaffMemberOnlyMixin, DeleteView):
    model = Product
    template_name = 'dashboard/product/product_confirm_delete.html'
    success_url = reverse_lazy('dashboard:products')

    def post(self, request, *args, **kwargs):
        result = self.delete(request, *args, **kwargs)
        messages.success(request, _('Deleted product %s') % self.object)
        return result


@staff_member_required
def stock_edit(request, product_pk, stock_pk=None):
    product = get_object_or_404(Product, pk=product_pk)
    if stock_pk:
        stock = get_object_or_404(Stock, pk=stock_pk)
    else:
        stock = Stock()
    form = forms.StockForm(request.POST or None, instance=stock,
                           product=product)
    if product.variants.exists():
        if form.is_valid():
            form.save()
            messages.success(request, _('Saved stock'))
            success_url = request.POST['success_url']
            return redirect(success_url)
        else:
            if form.errors:
                messages.error(request, _('Your submitted data was not valid - '
                                          'please correct the errors below'))
    else:
        messages.error(request, _(
            'You have to add at least one variant before you can add stock'))
    ctx = {'form': form,
           'product': product,
           'stock': stock}
    return TemplateResponse(request, 'dashboard/product/stock_form.html', ctx)


@staff_member_required
def stock_delete(request, product_pk, stock_pk):
    product = get_object_or_404(Product, pk=product_pk)
    stock = get_object_or_404(Stock, pk=stock_pk)
    if request.method == 'POST':
        stock.delete()
        messages.success(request, _('Deleted stock'))
        success_url = request.POST['success_url']
        return redirect(success_url)
    ctx = {'product': product,
           'stock': stock}
    return TemplateResponse(
        request, 'dashboard/product/stock_confirm_delete.html', ctx)


@staff_member_required
def product_image_edit(request, product_pk, img_pk=None):
    product = get_object_or_404(Product, pk=product_pk)
    if img_pk:
        product_image = get_object_or_404(product.images, pk=img_pk)
    else:
        product_image = ProductImage(product=product)
    form = forms.ProductImageForm(request.POST or None, request.FILES or None,
                                  instance=product_image)
    if form.is_valid():
        product_image = form.save()
        if img_pk:
            msg = _('Updated image %s') % product_image.image.name
        else:
            msg = _('Added image %s') % product_image.image.name
        messages.success(request, msg)
        success_url = request.POST['success_url']
        return redirect(success_url)
    else:
        if form.errors:
            messages.error(request, _('Your submitted data was not valid - '
                                      'please correct the errors below'))
    ctx = {'form': form,
           'product': product,
           'product_image': product_image}
    return TemplateResponse(
        request, 'dashboard/product/product_image_form.html', ctx)


@staff_member_required
def product_image_delete(request, product_pk, img_pk):
    product = get_object_or_404(Product, pk=product_pk)
    product_image = get_object_or_404(product.images, pk=img_pk)
    if request.method == 'POST':
        product_image.delete()
        messages.success(
            request, _('Deleted image %s') % product_image.image.name)
        success_url = request.POST['success_url']
        return redirect(success_url)
    ctx = {'product': product, 'product_image': product_image}
    return TemplateResponse(
        request, 'dashboard/product/product_image_confirm_delete.html', ctx)


@staff_member_required
def variant_edit(request, product_pk, variant_pk=None):
    product = get_object_or_404(Product.objects.select_subclasses(),
                                pk=product_pk)
    form_initial = {}
    if variant_pk:
        variant = get_object_or_404(product.variants.select_subclasses(),
                                    pk=variant_pk)
    else:
        variant = ProductVariant(product=product)
    form = forms.ProductVariantForm(request.POST or None, instance=variant,
                                    initial=form_initial)
    attribute_form = forms.VariantAttributeForm(request.POST or None,
                                                instance=variant)
    if all([form.is_valid(), attribute_form.is_valid()]):
        form.save()
        attribute_form.save()
        if variant_pk:
            msg = _('Updated variant %s') % variant.name
        else:
            msg = _('Added variant %s') % variant.name
        messages.success(request, msg)
        success_url = request.POST['success_url']
        return redirect(success_url)
    else:
        if any([form.is_valid(), attribute_form.is_valid()]):
            messages.error(request, _('Your submitted data was not valid - '
                                      'please correct the errors below'))
    ctx = {'attribute_form': attribute_form,
           'form': form,
           'product': product,
           'variant': variant}
    return TemplateResponse(request, 'dashboard/product/variant_form.html', ctx)


@staff_member_required
def variant_delete(request, product_pk, variant_pk):
    product = get_object_or_404(Product, pk=product_pk)
    variant = get_object_or_404(product.variants, pk=variant_pk)
    is_only_variant = product.variants.count() == 1
    if request.method == 'POST':
        variant.delete()
        messages.success(request, _('Deleted variant %s') % variant.name)
        success_url = request.POST['success_url']
        return redirect(success_url)
    ctx = {'is_only_variant': is_only_variant,
           'product': product,
           'variant': variant}
    return TemplateResponse(
        request, 'dashboard/product/product_variant_confirm_delete.html', ctx)


@staff_member_required
def attribute_list(request):
    attributes = ProductAttribute.objects.all()
    ctx = {'attributes': attributes}
    return TemplateResponse(request, 'dashboard/product/attributes/list.html',
                            ctx)


@staff_member_required
def attribute_edit(request, pk=None):
    if pk:
        attribute = get_object_or_404(ProductAttribute, pk=pk)
        title = attribute.display
    else:
        attribute = ProductAttribute()
        title = _('Add new attribute')
    form = forms.ProductAttributeForm(request.POST or None, instance=attribute)
    formset = forms.AttributeChoiceValueFormset(request.POST or None,
                                                request.FILES or None,
                                                instance=attribute)
    if form.is_valid() and formset.is_valid():
        attribute = form.save()
        formset.save()
        msg = _('Updated attribute') if pk else _('Added attribute')
        messages.success(request, msg)
        return redirect('dashboard:product-attribute-update', pk=attribute.pk)
    else:
        if form.errors or formset.errors:
            messages.error(request, _('Your submitted data was not valid - '
                                      'please correct the errors below'))
    ctx = {'attribute': attribute,
           'form': form,
           'formset': formset,
           'title': title}
    return TemplateResponse(request, 'dashboard/product/attributes/form.html',
                            ctx)


@staff_member_required
def attribute_delete(request, pk):
    attribute = get_object_or_404(ProductAttribute, pk=pk)
    if request.method == 'POST':
        attribute.delete()
        messages.success(request, _('Deleted attribute %s' % attribute.display))
        return redirect('dashboard:product-attributes')
    ctx = {'attribute': attribute}
    return TemplateResponse(request,
                            'dashboard/product/attributes/confirm_delete.html',
                            ctx)
