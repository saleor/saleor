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
import MultiAutocompleteSelectField, {
  MultiAutocompleteChoiceType
} from "@saleor/components/MultiAutocompleteSelectField";
import SingleAutocompleteSelectField from "@saleor/components/SingleAutocompleteSelectField";
import { ChangeEvent } from "@saleor/hooks/useForm";
import i18n from "@saleor/i18n";
import { maybe } from "@saleor/misc";
import { FormErrors } from "@saleor/types";

interface ChoiceType {
  label: string;
  value: string;
}
interface ProductType {
  hasVariants: boolean;
  id: string;
  name: string;
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

interface ProductOrganizationProps extends WithStyles<typeof styles> {
  canChangeType: boolean;
  categories?: ChoiceType[];
  categoryInputDisplayValue: string;
  collections?: ChoiceType[];
  data: {
    category: string;
    productType?: string;
  };
  disabled: boolean;
  errors: FormErrors<"productType" | "category">;
  selectedCollections: MultiAutocompleteChoiceType[];
  productType?: ProductType;
  productTypeInputDisplayValue?: string;
  productTypes?: ChoiceType[];
  fetchCategories: (query: string) => void;
  fetchCollections: (query: string) => void;
  onCategoryChange: (event: ChangeEvent) => void;
  onCollectionChange: (event: ChangeEvent) => void;
  onProductTypeChange?: (event: ChangeEvent) => void;
}

const ProductOrganization = withStyles(styles, { name: "ProductOrganization" })(
  ({
    canChangeType,
    categories,
    categoryInputDisplayValue,
    classes,
    collections,
    data,
    disabled,
    errors,
    fetchCategories,
    fetchCollections,
    selectedCollections,
    productType,
    productTypeInputDisplayValue,
    productTypes,
    onCategoryChange,
    onCollectionChange,
    onProductTypeChange
  }: ProductOrganizationProps) => (
    <Card className={classes.card}>
      <CardTitle title={i18n.t("Organize Product")} />
      <CardContent>
        {canChangeType ? (
          <SingleAutocompleteSelectField
            displayValue={productTypeInputDisplayValue}
            error={!!errors.productType}
            helperText={errors.productType}
            name="productType"
            disabled={disabled}
            label={i18n.t("Product Type")}
            choices={productTypes}
            value={data.productType}
            onChange={onProductTypeChange}
          />
        ) : (
          <>
            <Typography className={classes.label} variant="caption">
              {i18n.t("Product Type")}
            </Typography>
            <Typography>{maybe(() => productType.name, "...")}</Typography>
            <CardSpacer />
            <Typography className={classes.label} variant="caption">
              {i18n.t("Product Type")}
            </Typography>
            <Typography>
              {maybe(
                () =>
                  productType.hasVariants
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
          displayValue={categoryInputDisplayValue}
          error={!!errors.category}
          helperText={errors.category}
          disabled={disabled}
          label={i18n.t("Category")}
          choices={disabled ? [] : categories}
          name="category"
          value={data.category}
          onChange={onCategoryChange}
          fetchChoices={fetchCategories}
        />
        <FormSpacer />
        <Hr />
        <FormSpacer />
        <MultiAutocompleteSelectField
          displayValues={selectedCollections}
          label={i18n.t("Collections")}
          choices={disabled ? [] : collections}
          name="collections"
          value={selectedCollections.map(collection => collection.value)}
          helperText={i18n.t(
            "*Optional. Adding product to collection helps users find it."
          )}
          onChange={onCollectionChange}
          fetchChoices={fetchCollections}
        />
      </CardContent>
    </Card>
  )
);
ProductOrganization.displayName = "ProductOrganization";
export default ProductOrganization;
