import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { AttributeType, AttributeValueType } from "../..";
import CardTitle from "../../../components/CardTitle";
import { FormSpacer } from "../../../components/FormSpacer";
import MultiSelectField from "../../../components/MultiSelectField";
import SingleSelectField from "../../../components/SingleSelectField";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductOrganizationProps {
  categories?: Array<{ value: string; label: string }>;
  collections?: Array<{ value: string; label: string }>;
  attributes?: Array<{
    attribute: AttributeType;
    value: AttributeValueType;
  }>;
  category: string;
  productCollections: string[];
  data: {
    [key: string]: string;
  };
  disabled: boolean;
  errors: { [key: string]: string };
  product?: {
    productType?: {
      hasVariants?: boolean;
      name?: string;
    };
  };
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles(theme => ({
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
}));
const ProductOrganization = decorate<ProductOrganizationProps>(
  ({
    attributes,
    category,
    categories,
    classes,
    collections,
    data,
    disabled,
    errors,
    product,
    productCollections,
    onChange
  }) => (
    <Card>
      <CardTitle title={i18n.t("Organize Product")} />
      <CardContent>
        {product &&
        product.productType &&
        product.productType.name !== undefined ? (
          <SingleSelectField
            disabled={true}
            label={i18n.t("Product Type")}
            choices={[{ label: product.productType.name, value: "1" }]}
            value={"1"}
            onChange={() => {}}
          />
        ) : (
          <Skeleton />
        )}
        <FormSpacer />
        {product &&
        product.productType &&
        product.productType.hasVariants !== undefined ? (
          <SingleSelectField
            disabled={true}
            label={i18n.t("Is it configurable?")}
            choices={[
              { label: i18n.t("Yes"), value: "true" },
              { label: i18n.t("No"), value: "false" }
            ]}
            value={product.productType.hasVariants + ""}
            onChange={() => {}}
          />
        ) : (
          <Skeleton />
        )}
        <Typography className={classes.cardSubtitle}>
          {i18n.t("Attributes")}
        </Typography>
        {attributes ? (
          attributes.map((item, index) => {
            return (
              <React.Fragment key={index}>
                <SingleSelectField
                  disabled={disabled}
                  name={item.attribute.slug}
                  label={item.attribute.name}
                  onChange={onChange}
                  value={data[item.attribute.slug]}
                  choices={item.attribute.values.map(choice => ({
                    label: choice.name,
                    value: choice.slug
                  }))}
                  key={index}
                />
                <FormSpacer />
              </React.Fragment>
            );
          })
        ) : (
          <Skeleton />
        )}
        <hr className={classes.hr} />
        <SingleSelectField
          disabled={disabled}
          error={!!errors.category}
          hint={errors.category}
          label={i18n.t("Category")}
          choices={disabled ? [] : categories}
          name="category"
          value={category}
          onChange={onChange}
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
  )
);
ProductOrganization.displayName = "ProductOrganization";
export default ProductOrganization;
