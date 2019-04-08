import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import SingleAutocompleteSelectField from "../../../components/SingleAutocompleteSelectField";
import Skeleton from "../../../components/Skeleton";
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
  }: ProductVariantAttributesProps) => {
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
                <SingleAutocompleteSelectField
                  key={index}
                  disabled={disabled}
                  name={item.slug}
                  label={item.name}
                  onChange={handleAttributeValueSelect}
                  value={getAttributeValue(item.slug)}
                  choices={getAttributeValues(item.slug)}
                  custom
                />
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
