from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from . import forms
from ...userprofile.models import User


def superuser_or_first_run(u):
    if u.is_active and u.is_superuser:
        return True
    if not u.is_authenticated() and User.objects.count() == 0:
        return True
    return False
superuser_or_first_run = user_passes_test(
    superuser_or_first_run, login_url='registration:login')


@superuser_or_first_run
def setup(request):
    current_site = request.site
    current_domain = request.get_host()
    site_form = forms.SiteForm(
        request.POST or None, instance=current_site,
        current_domain=current_domain)
    all_forms = [site_form]
    if User.objects.count() == 0:
        admin_form = forms.CreateAdminForm(request.POST or None)
        all_forms.append(admin_form)
    else:
        admin_form = None
    if all(form.is_valid() for form in all_forms):
        for form in all_forms:
            form.save()
        return redirect('dashboard:index')
    return TemplateResponse(
        request, 'dashboard/setup/setup.html', {
            'site_form': site_form, 'admin_form': admin_form})
