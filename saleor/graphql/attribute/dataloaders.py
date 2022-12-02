from collections import defaultdict

from ...attribute.models import Attribute, AttributeValue
from ..core.dataloaders import DataLoader


class AttributeValuesByAttributeIdLoader(DataLoader):
    context_key = "attributevalues_by_attribute"

    def batch_load(self, keys):
        attribute_values = AttributeValue.objects.using(
            self.database_connection_name
        ).filter(attribute_id__in=keys)
        attribute_to_attributevalues = defaultdict(list)
        for attribute_value in attribute_values.iterator():
            attribute_to_attributevalues[attribute_value.attribute_id].append(
                attribute_value
            )
        return [attribute_to_attributevalues[attribute_id] for attribute_id in keys]


class AttributesByAttributeId(DataLoader):
    context_key = "attributes_by_id"

    def batch_load(self, keys):
        attributes = Attribute.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [attributes.get(key) for key in keys]


class AttributeValueByIdLoader(DataLoader):
    context_key = "attributevalue_by_id"

    def batch_load(self, keys):
        attribute_values = AttributeValue.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [attribute_values.get(attribute_value_id) for attribute_value_id in keys]
