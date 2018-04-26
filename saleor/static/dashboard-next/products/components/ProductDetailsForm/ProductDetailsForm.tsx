import Card, { CardContent } from "material-ui/Card";
import { withStyles } from "material-ui/styles";
import TextField from "material-ui/TextField";
import * as React from "react";

import { FormSpacer } from "../../../components/FormSpacer";
import PageHeader from "../../../components/PageHeader";
import PriceField from "../../../components/PriceField";
import { RichTextEditor } from "../../../components/RichTextEditor";
import i18n from "../../../i18n";

interface ProductDetailsFormProps {
  currencySymbol?: string;
  description?: string;
  loading?: boolean;
  name?: string;
  price?: string;
  onBack();
  onChange(event: any);
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridTemplateColumns: `1fr ${theme.spacing.unit}px 6rem`
  }
}));

export const ProductDetailsForm = decorate<ProductDetailsFormProps>(
  ({
    classes,
    currencySymbol,
    name,
    price,
    description,
    loading,
    onBack,
    onChange
  }) => (
    <Card>
      <PageHeader title={i18n.t("Edit product")} onBack={onBack} />
      <CardContent>
        <div className={classes.root}>
          <TextField
            disabled={loading}
            value={name}
            fullWidth
            label={i18n.t("Name")}
            name="name"
            onChange={onChange}
          />
          <span />
          <PriceField
            label={i18n.t("Price")}
            disabled={loading}
            value={price}
            onChange={onChange}
            currencySymbol={currencySymbol}
          />
        </div>
        <FormSpacer />
        <RichTextEditor
          label={i18n.t("Description")}
          fullWidth
          disabled={loading}
          value={description}
          helperText={i18n.t("Select text to enable text-formatting tools.")}
          onChange={onChange}
          name="description"
        />
      </CardContent>
    </Card>
  )
);
export default ProductDetailsForm;
