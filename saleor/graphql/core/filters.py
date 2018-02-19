from django import forms
from django_filters.constants import STRICTNESS
from graphene_django.filter.filterset import FilterSet


class DistinctFilterSet(FilterSet):
    # workaround for https://github.com/graphql-python/graphene-django/pull/290
    @property
    def qs(self):
        if not hasattr(self, '_qs'):
            if not self.is_bound:
                self._qs = self.queryset.all().distinct()
                return self._qs

            if not self.form.is_valid():
                if self.strict == STRICTNESS.RAISE_VALIDATION_ERROR:
                    raise forms.ValidationError(self.form.errors)
                elif self.strict == STRICTNESS.RETURN_NO_RESULTS:
                    self._qs = self.queryset.none()
                    return self._qs
                # else STRICTNESS.IGNORE...  ignoring

            # start with all the results and filter from there
            qs = self.queryset.all().distinct()
            for name, filter_ in self.filters.items():
                value = self.form.cleaned_data.get(name)

                if value is not None:  # valid & clean data
                    qs = filter_.filter(qs, value).distinct()

            self._qs = qs

        return self._qs
