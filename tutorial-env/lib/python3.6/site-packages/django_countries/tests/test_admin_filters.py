from __future__ import unicode_literals
from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import AnonymousUser

from django_countries import filters
from django_countries.tests import models

test_site = admin.AdminSite(name="test-admin")


class PersonAdmin(admin.ModelAdmin):
    list_filter = [("country", filters.CountryFilter)]


test_site.register(models.Person, PersonAdmin)


class TestCountryFilter(TestCase):
    def get_changelist_args(self, **kwargs):
        m = self.person_admin
        args = [
            kwargs.pop("list_display", m.list_display),
            kwargs.pop("list_display_links", m.list_display_links),
            kwargs.pop("list_filter", m.list_filter),
            kwargs.pop("date_hierarchy", m.date_hierarchy),
            kwargs.pop("search_fields", m.search_fields),
            kwargs.pop("list_select_related", m.list_select_related),
            kwargs.pop("list_per_page", m.list_per_page),
            kwargs.pop("list_max_show_all", m.list_max_show_all),
            kwargs.pop("list_editable", m.list_editable),
            m,
        ]
        if hasattr(m, "sortable_by"):  # Django 2.1+
            args.append(kwargs.pop("sortable_by", m.sortable_by))
        assert not kwargs, "Unexpected kwarg %s" % kwargs
        return args

    def setUp(self):
        models.Person.objects.create(name="Alice", country="NZ")
        models.Person.objects.create(name="Bob", country="AU")
        models.Person.objects.create(name="Chris", country="NZ")
        self.person_admin = PersonAdmin(models.Person, test_site)

    def test_filter_none(self):
        request = RequestFactory().get("/person/")
        request.user = AnonymousUser()
        cl = ChangeList(request, models.Person, *self.get_changelist_args())
        cl.get_results(request)
        self.assertEqual(list(cl.result_list), list(models.Person.objects.all()))

    def test_filter_country(self):
        request = RequestFactory().get("/person/", data={"country": "NZ"})
        request.user = AnonymousUser()
        cl = ChangeList(request, models.Person, *self.get_changelist_args())
        cl.get_results(request)
        self.assertEqual(
            list(cl.result_list), list(models.Person.objects.exclude(country="AU"))
        )

    def test_choices(self):
        request = RequestFactory().get("/person/", data={"country": "NZ"})
        request.user = AnonymousUser()
        cl = ChangeList(request, models.Person, *self.get_changelist_args())
        choices = list(cl.filter_specs[0].choices(cl))
        self.assertEqual(
            [c["display"] for c in choices], ["All", "Australia", "New Zealand"]
        )
        for choice in choices:
            self.assertEqual(choice["selected"], choice["display"] == "New Zealand")
