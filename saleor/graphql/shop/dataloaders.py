from ..attribute.dataloaders import AttributesByAttributeId
from ..core.dataloaders import DataLoader
from ..product.dataloaders import AttributeCategoriesBySiteSettingsIdLoader


class CategoryAttributeBySiteSettingsIdLoader(DataLoader):
    """Load category attributes settings by site settings ID."""

    context_key = "category_attributes_by_sitesettings"

    def batch_load(self, keys):
        def with_attributes(attribute_categories):
            site_settings_to_attributes_map = {}
            attribute_ids = []
            for site_settings, cat_attrs in zip(keys, attribute_categories):
                site_attr_ids = [cat_attr.attribute_id for cat_attr in cat_attrs]
                attribute_ids.extend(site_attr_ids)
                site_settings_to_attributes_map[site_settings] = site_attr_ids

            def map_attributes(attributes):
                attributes_map = {attr.id: attr for attr in attributes}
                return [
                    [
                        attributes_map[attr_id]
                        for attr_id in site_settings_to_attributes_map[site_settings_id]
                    ]
                    for site_settings_id in keys
                ]

            return (
                AttributesByAttributeId(self.context)
                .load_many(attribute_ids)
                .then(map_attributes)
            )

        return (
            AttributeCategoriesBySiteSettingsIdLoader(self.context)
            .load_many(keys)
            .then(with_attributes)
        )
