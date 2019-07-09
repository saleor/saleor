import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import SingleAutocompleteSelectField from "@saleor/components/SingleAutocompleteSelectField";
import Skeleton from "@saleor/components/Skeleton";
import i18n from "../../../i18n";
import { ProductVariant_attributes_attribute } from "../../types/ProductVariant";

const styles = (theme: Theme) =>
  createStyles({
    card: {
      overflow: "visible"
    },
    grid: {
      display: "grid",
      gridColumnGap: `${theme.spacing.unit * 2}px`,
      gridRowGap: `${theme.spacing.unit * 3}px`,
      gridTemplateColumns: "1fr 1fr"
    }
  });

interface ProductVariantAttributesProps extends WithStyles<typeof styles> {
  attributes?: ProductVariant_attributes_attribute[];
  data: {
    attributes?: Array<{
      name: string;
      slug: string;
      value: string;
    }>;
  };
  disabled: boolean;
  onChange: (
    event: React.ChangeEvent<{
      name: string;
      value: Array<{
        slug: string;
        value: string;
      }>;
    }>
  ) => void;
}

const ProductVariantAttributes = withStyles(styles, {
  name: "ProductVariantAttributes"
})(
  ({
    attributes,
    classes,
    data,
    disabled,
    onChange
  }: ProductVariantAttributesProps) => (
    <Card className={classes.card}>
      <CardTitle title={i18n.t("General Information")} />
      <CardContent className={classes.grid}>
        {attributes === undefined &&
        (console.log(data) || data.attributes.length) === 0 ? (
          <Skeleton />
        ) : (
          data.attributes.map((attribute, attributeIndex) => {
            const getAttributeValue = (slug: string) => {
              const valueMatch = attributes.find(a => a.slug === slug);
              if (valueMatch) {
                const value = data.attributes.find(a => a.slug === slug).value;
                const labelMatch = valueMatch.values.find(
                  v => v.slug === value
                );
                const label = labelMatch ? labelMatch.name : value;
                return {
                  label,
                  value
                };
              }
              return {
                label: "",
                value: ""
              };
            };
            const getAttributeValues = (slug: string) => {
              const matches = attributes.filter(a => a.slug === slug);
              return matches.length > 0
                ? matches[0].values.map(v => ({
                    label: v.name,
                    value: v.slug
                  }))
                : [];
            };
            const handleAttributeValueSelect = (
              event: React.ChangeEvent<{
                name: string;
                value: {
                  label: string;
                  value: string;
                };
              }>
            ) =>
              onChange({
                ...(event as any),
                target: {
                  ...event.target,
                  name: "attributes",
                  value: data.attributes.map(a =>
                    a.slug === event.target.name
                      ? {
                          name: a.name,
                          slug: a.slug,
                          value: event.target.value.value
                        }
                      : a
                  )
                }
              });

            return (
              <SingleAutocompleteSelectField
                key={attributeIndex}
                disabled={disabled}
                name={attribute.slug}
                label={attribute.name}
                onChange={handleAttributeValueSelect}
                value={getAttributeValue(attribute.slug)}
                choices={getAttributeValues(attribute.slug)}
                custom
              />
            );
          })
        )}
      </CardContent>
    </Card>
  )
);
ProductVariantAttributes.displayName = "ProductVariantAttributes";
export default ProductVariantAttributes;
