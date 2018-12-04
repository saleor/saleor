import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import { FormSpacer } from "../../../components/FormSpacer";
import SingleAutocompleteSelectField from "../../../components/SingleAutocompleteSelectField";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { ProductVariant_attributes_attribute } from "../../types/ProductVariant";

interface ProductVariantAttributesProps {
  attributes?: ProductVariant_attributes_attribute[];
  data: {
    attributes?: Array<{
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

const decorate = withStyles(theme => ({
  card: {
    overflow: "visible" as "visible"
  },
  grid: {
    display: "grid",
    gridGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "1fr 1fr"
  }
}));

const ProductVariantAttributes = decorate<ProductVariantAttributesProps>(
  ({ attributes, classes, data, disabled, onChange }) => {
    return (
      <Card className={classes.card}>
        <CardTitle title={i18n.t("General Information")} />
        <CardContent className={classes.grid}>
          {attributes === undefined ? (
            <Skeleton />
          ) : (
            attributes.map((item, index) => {
              const getAttributeValue = (slug: string) => {
                const valueMatches = attributes.filter(a => a.slug === slug);
                if (valueMatches.length > 0) {
                  const value = data.attributes.filter(a => a.slug === slug)[0]
                    .value;
                  const labelMatches = valueMatches[0].values.filter(
                    v => v.slug === value
                  );
                  const label =
                    labelMatches.length > 0 ? labelMatches[0].name : value;
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
                        ? { slug: a.slug, value: event.target.value.value }
                        : a
                    )
                  }
                });

              return (
                <React.Fragment key={index}>
                  <SingleAutocompleteSelectField
                    disabled={disabled}
                    name={item.slug}
                    label={item.name}
                    onChange={handleAttributeValueSelect}
                    value={getAttributeValue(item.slug)}
                    choices={getAttributeValues(item.slug)}
                    key={index}
                    custom
                  />
                  <FormSpacer />
                </React.Fragment>
              );
            })
          )}
        </CardContent>
      </Card>
    );
  }
);
ProductVariantAttributes.displayName = "ProductVariantAttributes";
export default ProductVariantAttributes;
