from ..product.models import ProductAttribute, AttributeChoiceValue


class AttributeAggregation(object):
    field = 'attributes_filter'
    attribute_id = None
    aggregation_name = None

    def __init__(self, attribute_name):
        self.attribute = ProductAttribute.objects.get(name=attribute_name)
        self.attribute_id = self.attribute.pk
        self.aggregation_name = self.attribute.name

    def __repr__(self):
        return 'AttribtueAggregation(attribute_name=%s)' % self.aggregation_name

    def get_aggs(self):
        terms_field = '%s.%s' % (self.field, self.attribute_id)
        return {"terms": {"field": "%s" % terms_field}}

    def parse_results(self, aggregations_results):
        # parse aggregations part of the response to list of attr ids
        buckets = aggregations_results[self.aggregation_name]['buckets']
        result_map = {bucket['key']: bucket['doc_count'] for bucket in buckets}
        all_values = AttributeChoiceValue.objects.filter(
            pk__in=result_map.keys())

        return {
            'attribute': self.attribute,
            'values': {
                attr_value: result_map[str(attr_value.pk)]
                for attr_value in all_values
            }
        }

