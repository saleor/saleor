import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import FormSpacer from "../../../components/FormSpacer";
import RichTextEditor from "../../../components/RichTextEditor";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ProductDetails_product } from "../../types/ProductDetails";
import { FormData as CreateFormData } from "../ProductCreatePage";
import { FormData as UpdateFormData } from "../ProductUpdatePage";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: `3fr 1fr`
    }
  });

interface ProductDetailsFormProps extends WithStyles<typeof styles> {
  data: CreateFormData & UpdateFormData;
  disabled?: boolean;
  errors: { [key: string]: string };
  product?: ProductDetails_product;
  onChange(event: any);
}

export const ProductDetailsForm = withStyles(styles, {
  name: "ProductDetailsForm"
})(
  ({
    classes,
    data,
    disabled,
    errors,
    product,
    onChange
  }: ProductDetailsFormProps) => (
    <Card>
      <CardTitle title={i18n.t("General information")} />
      <CardContent>
        <div className={classes.root}>
          <TextField
            error={!!errors.name}
            helperText={errors.name}
            disabled={disabled}
            fullWidth
            label={i18n.t("Name")}
            name="name"
            rows={5}
            value={data.name}
            onChange={onChange}
          />
        </div>
        <FormSpacer />
        <RichTextEditor
          disabled={disabled}
          error={!!errors.descriptionJson}
          helperText={errors.descriptionJson}
          initial={maybe(() => JSON.parse(product.descriptionJson), null)}
          label={i18n.t("Description")}
          name="description"
          onChange={onChange}
        />
      </CardContent>
    </Card>
  )
);
ProductDetailsForm.displayName = "ProductDetailsForm";
export default ProductDetailsForm;
