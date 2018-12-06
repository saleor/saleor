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

import CardTitle from "../../../components/CardTitle";
import { FormSpacer } from "../../../components/FormSpacer";
import MultiSelectField from "../../../components/MultiSelectField";
import SingleAutocompleteSelectField from "../../../components/SingleAutocompleteSelectField";
import SingleSelectField from "../../../components/SingleSelectField";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ProductCreateData_productTypes_edges_node_productAttributes } from "../../types/ProductCreateData";

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
      margin: `${theme.spacing.unit * 3}px 0`
    },
    hr: {
      backgroundColor: "#eaeaea",
      border: "none",
      height: 1,
      margin: `0 -${theme.spacing.unit * 3}px ${theme.spacing.unit * 3}px`
    }
  });

interface ProductOrganizationProps extends WithStyles<typeof styles> {
  categories?: Array<{ value: string; label: string }>;
  collections?: Array<{ value: string; label: string }>;
  productCollections: string[];
  data: {
    attributes: Array<{
      slug: string;
      value: string;
    }>;
    category: {
      label: string;
      value: string;
    };
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
  onChange: (event: React.ChangeEvent<any>) => void;
}

const ProductOrganization = withStyles(styles, { name: "ProductOrganization" })(
  ({
    categories,
    classes,
    collections,
    data,
    disabled,
    errors,
    fetchCategories,
    product,
    productCollections,
    productTypes,
    onChange
  }: ProductOrganizationProps) => {
    const unrolledAttributes = maybe(
      () => data.productType.value.productAttributes,
      []
    );
    const getAttributeName = (slug: string) =>
      unrolledAttributes.filter(a => a.slug === slug)[0].name;
    const getAttributeValue = (slug: string) => {
      if (unrolledAttributes.length > 0) {
        const value = data.attributes.filter(a => a.slug === slug)[0];
        const matches = unrolledAttributes
          .filter(a => a.slug === slug)[0]
          .values.filter(v => v.slug === value.value);
        const label = matches.length > 0 ? matches[0].name : value.value;
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
    const getAttributeValues = (slug: string) =>
      unrolledAttributes.filter(a => a.slug === slug)[0].values;
    const handleProductTypeSelect = (
      event: React.ChangeEvent<{
        name: string;
        value: {
          label: string;
          value: ProductType;
        };
      }>
    ) => {
      onChange(event);
      onChange({
        ...event,
        target: {
          ...event.target,
          name: "attributes",
          value: event.target.value.value.productAttributes.map(attribute => ({
            slug: attribute.slug,
            value: ""
          }))
        }
      });
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
          <SingleAutocompleteSelectField
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
          <FormSpacer />
          <SingleSelectField
            disabled={true}
            name="hasVariants"
            label={i18n.t("Is it configurable?")}
            choices={[
              { label: i18n.t("Yes"), value: "true" },
              { label: i18n.t("No"), value: "false" }
            ]}
            value={
              product &&
              product.productType &&
              product.productType.hasVariants !== undefined
                ? product.productType.hasVariants + ""
                : data.productType
                ? data.productType.value.hasVariants + ""
                : false + ""
            }
            onChange={onChange}
          />
          <Typography className={classes.cardSubtitle}>
            {i18n.t("Attributes")}
          </Typography>
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
          <MultiSelectField
            disabled={disabled}
            error={!!errors.collections}
            hint={errors.collections}
            label={i18n.t("Collections")}
            choices={disabled ? [] : collections}
            name="collections"
            value={productCollections}
            onChange={onChange}
          />
        </CardContent>
      </Card>
    );
  }
);
ProductOrganization.displayName = "ProductOrganization";
export default ProductOrganization;
