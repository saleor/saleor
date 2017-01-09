from django import forms

from .backends import get_search_backend
from .aggregations import AttributeAggregation


class SearchForm(forms.Form):
    q = forms.CharField(label='Query', required=True)
    color_filter = forms.MultipleChoiceField(required=False)
    collar_filter = forms.MultipleChoiceField(required=False)
    aggregations = {
        'color': AttributeAggregation(attribute_name='color'),
        'collar': AttributeAggregation(attribute_name='collar')
    }
    agg_to_filter_map = {
        'color': 'color_filter',
        'collar': 'collar_filter',
    }

    def search(self, model_or_queryset):
        backend = get_search_backend('default')
        query = self.cleaned_data['q']
        results, aggregations = backend.search(
            query, model_or_queryset=model_or_queryset,
            aggregations=self.aggregations)
        self.update_filter_fields(aggregations)
        return results, aggregations

    def update_filter_fields(self, aggregations):
        for agg_name, agg_data in aggregations.items():
            field_name = self.agg_to_filter_map[agg_name]
            agg_instance = self.aggregations[agg_name]
            agg_instance.update_field(
                self.fields[field_name], agg_data['values'])
