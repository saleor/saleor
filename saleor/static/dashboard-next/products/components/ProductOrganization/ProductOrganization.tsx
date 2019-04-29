import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import CardTitle from "../../../components/CardTitle";
import { FormSpacer } from "../../../components/FormSpacer";
import MultiAutocompleteSelectField from "../../../components/MultiAutocompleteSelectField";
import SingleAutocompleteSelectField from "../../../components/SingleAutocompleteSelectField";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ProductCreateData_productTypes_edges_node_productAttributes } from "../../types/ProductCreateData";

interface ChoiceType {
  label: string;
  value: string;
}
interface ProductType {
  hasVariants: boolean;
  id: string;
  name: string;
  productAttributes: ProductCreateData_productTypes_edges_node_productAttributes[];
}

const styles = (theme: Theme) =>
  createStyles({
    card: {
      overflow: "visible"
    },
    cardSubtitle: {
      fontSize: "1rem",
      marginBottom: theme.spacing.unit / 2
    },
    hr: {
      backgroundColor: theme.overrides.MuiCard.root.borderColor,
      border: "none",
      height: 1,
      margin: `0 -${theme.spacing.unit * 3}px ${theme.spacing.unit * 3}px`
    },
    label: {
      marginBottom: theme.spacing.unit / 2
    }
  });

interface ProductOrganizationProps extends WithStyles<typeof styles> {
  canChangeType: boolean;
  categories?: Array<{ value: string; label: string }>;
  collections?: Array<{ value: string; label: string }>;
  data: {
    attributes: Array<{
      slug: string;
      value: string;
    }>;
    category: ChoiceType;
    collections: ChoiceType[];
    productType: {
      label: string;
      value: {
        hasVariants: boolean;
        id: string;
        name: string;
        productAttributes: ProductCreateData_productTypes_edges_node_productAttributes[];
      };
    };
  };
  disabled: boolean;
  errors: { [key: string]: string };
  product?: {
    productType?: {
      hasVariants?: boolean;
      name?: string;
    };
  };
  productTypes?: ProductType[];
  fetchCategories: (query: string) => void;
  fetchCollections: (query: string) => void;
  onChange: (event: React.ChangeEvent<any>, cb?: () => void) => void;
}

const ProductOrganization = withStyles(styles, { name: "ProductOrganization" })(
  ({
    canChangeType,
    categories,
    classes,
    collections,
    data,
    disabled,
    errors,
    fetchCategories,
    fetchCollections,
    product,
    productTypes,
    onChange
  }: ProductOrganizationProps) => {
    const unrolledAttributes = maybe(
      () => data.productType.value.productAttributes,
      []
    );
    const getAttributeName = (slug: string) => {
      const match = unrolledAttributes.find(a => a.slug === slug);
      if (!match) {
        return "";
      }
      return match.name;
    };
    const getAttributeValue = (slug: string) => {
      if (unrolledAttributes.length > 0) {
        const value = data.attributes.find(a => a.slug === slug);
        const attributeMatch = unrolledAttributes.find(a => a.slug === slug);
        if (!attributeMatch) {
          return {
            label: "",
            value: ""
          };
        }
        const attributeValueMatch = attributeMatch.values.find(
          v => v.slug === value.value
        );
        const label = !!attributeValueMatch
          ? attributeValueMatch.name
          : value.value;
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
      const match = unrolledAttributes.find(a => a.slug === slug);
      if (match) {
        return match.values;
      }

      return [];
    };
    const handleProductTypeSelect = (
      event: React.ChangeEvent<{
        name: string;
        value: {
          label: string;
          value: ProductType;
        };
      }>
    ) => {
      onChange(event, () =>
        onChange({
          ...event,
          target: {
            ...event.target,
            name: "attributes",
            value: event.target.value.value.productAttributes.map(
              attribute => ({
                slug: attribute.slug,
                value: ""
              })
            )
          }
        })
      );
    };
    const handleAttributeValueSelect = (
      event: React.ChangeEvent<{
        name: string;
        value: {
          label: string;
          value: string;
        };
      }>
    ) => {
      onChange({
        ...event,
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
    };
    return (
      <Card className={classes.card}>
        <CardTitle title={i18n.t("Organize Product")} />
        <CardContent>
          {canChangeType ? (
            <SingleAutocompleteSelectField
              error={!!errors.productType}
              helperText={errors.productType}
              name="productType"
              disabled={!!product || disabled}
              label={i18n.t("Product Type")}
              choices={
                product &&
                product.productType &&
                product.productType.name !== undefined
                  ? [{ label: product.productType.name, value: "1" }]
                  : productTypes
                  ? productTypes.map(pt => ({ label: pt.name, value: pt }))
                  : []
              }
              value={data.productType}
              onChange={handleProductTypeSelect}

            />
          ) : (
            <>
              <Typography className={classes.label} variant="caption">
                {i18n.t("Product Type")}
              </Typography>
              <Typography>
                {maybe(() => product.productType.name, "...")}
              </Typography>
              <CardSpacer />
              <Typography className={classes.label} variant="caption">
                {i18n.t("Product Type")}
              </Typography>
              <Typography>
                {maybe(
                  () =>
                    product.productType.hasVariants
                      ? i18n.t("Configurable")
                      : i18n.t("Simple"),
                  "..."
                )}
              </Typography>
            </>
          )}
          {!(data && data.attributes && data.attributes.length === 0) ? (
            <>
              <CardSpacer />
              <Typography className={classes.cardSubtitle}>
                {i18n.t("Attributes")}
              </Typography>
              <hr className={classes.hr} />
            </>
          ) : (
            <FormSpacer />
          )}
          {data.attributes ? (
            data.attributes.map((item, index) => {
              return (
                <React.Fragment key={index}>
                  <SingleAutocompleteSelectField
                    disabled={disabled}
                    name={item.slug}
                    label={getAttributeName(item.slug)}
                    onChange={handleAttributeValueSelect}
                    value={getAttributeValue(item.slug)}
                    choices={getAttributeValues(item.slug).map(v => ({
                      label: v.name,
                      value: v.slug
                    }))}
                    custom
                  />
                  <FormSpacer />
                </React.Fragment>
              );
            })
          ) : (
            <Skeleton />
          )}
          <hr className={classes.hr} />
          <SingleAutocompleteSelectField
            error={!!errors.category}
            helperText={errors.category}
            disabled={disabled}
            label={i18n.t("Category")}
            choices={disabled ? [] : categories}
            name="category"
            value={data.category}
            onChange={onChange}
            fetchChoices={fetchCategories}
          />
          <FormSpacer />
          <hr className={classes.hr} />
          <MultiAutocompleteSelectField
            label={i18n.t("Collections")}
            choices={disabled ? [] : collections}
            name="collections"
            value={data.collections}
            onChange={onChange}
            fetchChoices={fetchCollections}
          />
        </CardContent>
      </Card>
    );
  }
);
ProductOrganization.displayName = "ProductOrganization";
export default ProductOrganization;
