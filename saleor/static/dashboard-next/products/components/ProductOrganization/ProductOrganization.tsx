import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import React from "react";

import CardSpacer from "@saleor/components/CardSpacer";
import CardTitle from "@saleor/components/CardTitle";
import { FormSpacer } from "@saleor/components/FormSpacer";
import Hr from "@saleor/components/Hr";
import MultiAutocompleteSelectField from "@saleor/components/MultiAutocompleteSelectField";
import SingleAutocompleteSelectField from "@saleor/components/SingleAutocompleteSelectField";
import { ChangeEvent } from "@saleor/hooks/useForm";
import i18n from "@saleor/i18n";
import { maybe } from "@saleor/misc";
import { FormErrors } from "@saleor/types";
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
    label: {
      marginBottom: theme.spacing.unit / 2
    }
  });

interface ProductOrganizationFormData {
  attributes: Array<{
    slug: string;
    values: string[];
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
}

interface ProductOrganizationProps extends WithStyles<typeof styles> {
  canChangeType: boolean;
  categories?: Array<{ value: string; label: string }>;
  collections?: Array<{ value: string; label: string }>;
  collectionInputDisplayValue: string;
  data: {
    attributes: Array<{
      slug: string;
      values: string[];
    }>;
    category: ChoiceType;
    collections: string[];
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
  errors: FormErrors<"productType" | "category">;
  product?: {
    productType?: {
      hasVariants?: boolean;
      name?: string;
    };
  };
  productTypes?: ProductType[];
  fetchCategories: (query: string) => void;
  fetchCollections: (query: string) => void;
  onChange: (event: ChangeEvent<any>) => void;
  onCollectionChange: (event: ChangeEvent<any>) => void;
  onSet: (data: Partial<ProductOrganizationFormData>) => void;
}

const ProductOrganization = withStyles(styles, { name: "ProductOrganization" })(
  ({
    canChangeType,
    categories,
    classes,
    collections,
    collectionInputDisplayValue,
    data,
    disabled,
    errors,
    fetchCategories,
    fetchCollections,
    product,
    productTypes,
    onChange,
    onCollectionChange,
    onSet
  }: ProductOrganizationProps) => {
    const handleProductTypeSelect = (
      event: ChangeEvent<
        string,
        {
          label: string;
          value: ProductType;
        }
      >
    ) => {
      onSet({
        attributes: event.target.value.value.productAttributes.map(
          attribute => ({
            slug: attribute.slug,
            values: [""]
          })
        ),
        productType: event.target.value
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
              disabled={disabled}
              label={i18n.t("Product Type")}
              choices={maybe(
                () => productTypes.map(pt => ({ label: pt.name, value: pt })),
                []
              )}
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
          <FormSpacer />
          <Hr />
          <FormSpacer />
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
          <Hr />
          <FormSpacer />
          <MultiAutocompleteSelectField
            displayValue={collectionInputDisplayValue}
            label={i18n.t("Collections")}
            choices={disabled ? [] : collections}
            name="collections"
            value={data.collections}
            helperText={i18n.t(
              "*Optional. Adding product to collection helps users find it."
            )}
            onChange={onCollectionChange}
            fetchChoices={fetchCollections}
          />
        </CardContent>
      </Card>
    );
  }
);
ProductOrganization.displayName = "ProductOrganization";
export default ProductOrganization;
