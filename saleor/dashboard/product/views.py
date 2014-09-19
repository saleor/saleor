from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import ListView, UpdateView
from django.views.generic.edit import FormMixin
from django.utils.translation import ugettext_lazy as _
from ..views import StaffMemberOnlyMixin
from ...product.models import Product
from .forms import (ProductImageFormSet, ProductForm, ProductCategory,
                    get_product_form_class, get_variant_formset_class)


class ProductListView(StaffMemberOnlyMixin, ListView, FormMixin):
    model = Product
    paginate_by = 30
    template_name = 'dashboard/product/list.html'
    context_object_name = 'products'
    form_class = ProductCategory

    def get_queryset(self):
        qs = super(ProductListView, self).get_queryset()
        qs = qs.prefetch_related(
            'stockrecords', 'images').select_related('brand')
        qs = qs.select_subclasses()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super(ProductListView, self).get_context_data(**kwargs)
        ctx['form'] = self.form_class()
        return ctx

    def post(self, request, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid:
            return HttpResponseRedirect(reverse('dashboard:product-add'))
        return self.get(request, **kwargs)


class ProductView(StaffMemberOnlyMixin, UpdateView):
    model = Product
    template_name = 'dashboard/product/product_form.html'
    image_formset = ProductImageFormSet
    variant_formset = None
    form_class = ProductForm
    context_object_name = 'product'

    def __init__(self, *args, **kwargs):
        super(ProductView, self).__init__(*args, **kwargs)
        self.formsets = {'image_formset': self.image_formset}

    def get_queryset(self):
        qs = super(UpdateView, self).get_queryset()
        qs = qs.select_subclasses()
        return qs

    def get_object(self, queryset=None):
        self.creating = 'pk' not in self.kwargs
        if self.creating:
            return None
        else:
            product = super(ProductView, self).get_object(queryset)
            if not self.variant_formset:
                variant_formset_cls = get_variant_formset_class(product)
                self.formsets['variant_formset'] = variant_formset_cls
                self.variant_formset = variant_formset_cls
            return product

    def get_form_class(self):
        product = self.get_object()
        return get_product_form_class(product)

    def get_context_data(self, **kwargs):
        ctx = super(ProductView, self).get_context_data(**kwargs)

        for ctx_name, formset_class in self.formsets.items():
            if ctx_name not in ctx:
                ctx[ctx_name] = formset_class(instance=self.object)

        if self.object is None:
            ctx['title'] = 'Add new product'
        else:
            ctx['title'] = ctx['product'].name
        return ctx

    def process_all_forms(self, form):
        if self.creating and form.is_valid():
            self.object = form.save()

        formsets = {}
        for ctx_name, formset_class in self.formsets.items():
            formsets[ctx_name] = formset_class(self.request.POST,
                                               self.request.FILES,
                                               instance=self.object)
        for formset in formsets.values():
            formset.is_valid()

        is_valid = form.is_valid() \
            and all([formset.is_valid() for formset in formsets.values()])

        if is_valid:
            return self.forms_valid(form, formsets)
        else:
            return self.forms_invalid(form, formsets)

    form_valid = form_invalid = process_all_forms

    def forms_valid(self, form, formsets):
        if not self.creating:
            self.object = form.save()
        for formset in formsets.values():
            formset.save()
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, formsets):
        if self.creating and self.object and self.object.pk is not None:
            self.object.delete()
            self.object = None

        messages.error(self.request,
                       _("Your submitted data was not valid - please "
                         "correct the errors below"))
        ctx = self.get_context_data(form=form, **formsets)
        return self.render_to_response(ctx)

    def get_success_url(self):
        return reverse('dashboard:product-update',
                       kwargs={'pk': self.object.pk})
