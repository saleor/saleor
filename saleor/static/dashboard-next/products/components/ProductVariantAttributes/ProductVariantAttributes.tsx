import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import Grid from "@saleor/components/Grid";
import SingleAutocompleteSelectField, {
  SingleAutocompleteChoiceType
} from "@saleor/components/SingleAutocompleteSelectField";
import Skeleton from "@saleor/components/Skeleton";
import { FormsetAtomicData, FormsetChange } from "@saleor/hooks/useFormset";
import i18n from "../../../i18n";
import { ProductVariant_attributes_attribute_values } from "../../types/ProductVariant";

export interface VariantAttributeInputData {
  values: ProductVariant_attributes_attribute_values[];
}
export type VariantAttributeInput = FormsetAtomicData<
  VariantAttributeInputData,
  string
>;

interface ProductVariantAttributesProps {
  attributes: VariantAttributeInput[];
  disabled: boolean;
  errors: Record<string, string>;
  onChange: FormsetChange<VariantAttributeInputData>;
}

function getAttributeDisplayValue(
  id: string,
  slug: string,
  attributes: VariantAttributeInput[]
): string {
  const attribute = attributes.find(attr => attr.id === id);
  const attributeValue = attribute.data.values.find(
    value => value.slug === slug
  );
  if (!!attributeValue) {
    return attributeValue.name;
  }

  return slug;
}

function getAttributeValue(
  id: string,
  attributes: VariantAttributeInput[]
): string {
  const attribute = attributes.find(attr => attr.id === id);
  return attribute.value;
}

function getAttributeValueChoices(
  id: string,
  attributes: VariantAttributeInput[]
): SingleAutocompleteChoiceType[] {
  const attribute = attributes.find(attr => attr.id === id);
  return attribute.data.values.map(attributeValue => ({
    label: attributeValue.name,
    value: attributeValue.slug
  }));
}

const ProductVariantAttributes: React.FC<ProductVariantAttributesProps> = ({
  attributes,
  disabled,
  errors,
  onChange
}) => (
  <Card>
    <CardTitle title={i18n.t("General Information")} />
    <CardContent>
      <Grid variant="uniform">
        {attributes === undefined ? (
          <Skeleton />
        ) : (
          attributes.map((attribute, attributeIndex) => {
            return (
              <SingleAutocompleteSelectField
                key={attributeIndex}
                disabled={disabled}
                displayValue={getAttributeDisplayValue(
                  attribute.id,
                  attribute.value,
                  attributes
                )}
                error={!!errors[attribute.id]}
                helperText={errors[attribute.id]}
                label={attribute.label}
                name={`attribute:${attribute.id}`}
                onChange={event => onChange(attribute.id, event.target.value)}
                value={getAttributeValue(attribute.id, attributes)}
                choices={getAttributeValueChoices(attribute.id, attributes)}
                allowCustomValues
              />
            );
          })
        )}
      </Grid>
    </CardContent>
  </Card>
);
ProductVariantAttributes.displayName = "ProductVariantAttributes";
export default ProductVariantAttributes;
