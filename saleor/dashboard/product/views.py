from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import ListView, UpdateView
from django.utils.translation import ugettext_lazy as _
from ..stock.forms import StockRecordFormSet
from ..views import StaffMemberOnlyMixin
from ...product.models import Product
from .forms import ProductImageFormSet


class ProductListView(StaffMemberOnlyMixin, ListView):
    model = Product
    paginate_by = 30
    template_name = 'dashboard/product/list.html'
    context_object_name = 'products'

    def get_queryset(self):
        qs = super(ProductListView, self).get_queryset()
        qs = qs.prefetch_related('stockrecords', 'images').select_related('brand')

        return qs


class ProductView(StaffMemberOnlyMixin, UpdateView):
    model = Product
    template_name = 'dashboard/product/product_form.html'
    image_formset = ProductImageFormSet
    stock_formset = StockRecordFormSet

    def __init__(self, *args, **kwargs):
        super(ProductView, self).__init__(*args, **kwargs)
        self.formsets = {'image_formset': self.image_formset,
                         'stock_formset': self.stock_formset}

    def get_object(self, queryset=None):
        """
        This parts allows generic.UpdateView to handle creating products as
        well. The only distinction between an UpdateView and a CreateView
        is that self.object is None. We emulate this behavior.
        Additionally, self.product_class is set.
        """
        self.creating = 'pk' not in self.kwargs

        if self.creating:
            return None  # success
        else:
            product = super(ProductView, self).get_object(queryset)
            return product

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
        """
        Short-circuits the regular logic to have one place to have our
        logic to check all forms
        """
        if self.creating and form.is_valid():
            self.object = form.save()

        formsets = {}
        for ctx_name, formset_class in self.formsets.items():
            formsets[ctx_name] = formset_class(self.request.POST,
                                               self.request.FILES,
                                               instance=self.object)

        is_valid = form.is_valid() and all([formset.is_valid()
                                            for formset in formsets.values()])

        if is_valid:
            return self.forms_valid(form, formsets)
        else:
            return self.forms_invalid(form, formsets)

    # form_valid and form_invalid are called depending on the validation result
    # of just the product form and redisplay the form respectively return a
    # redirect to the success URL. In both cases we need to check our formsets
    # as well, so both methods do the same. process_all_forms then calls
    # forms_valid or forms_invalid respectively, which do the redisplay or
    # redirect.
    form_valid = form_invalid = process_all_forms

    def forms_valid(self, form, formsets):
        """
        Save all changes and display a success url.
        """
        if not self.creating:
            # a just created product was already saved in process_all_forms()
            self.object = form.save()

        # Save formsets
        for formset in formsets.values():
            formset.save()

        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, formsets):
        # delete the temporary product again
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

