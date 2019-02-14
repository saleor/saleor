import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import { RawDraftContentState } from "draft-js";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import FormSpacer from "../../../components/FormSpacer";
import RichTextEditor from "../../../components/RichTextEditor";
import i18n from "../../../i18n";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: `3fr 1fr`
    }
  });

interface ProductDetailsFormProps extends WithStyles<typeof styles> {
  data: {
    description: RawDraftContentState;
    name: string;
  };
  disabled?: boolean;
  errors: { [key: string]: string };
  onChange(event: any);
}

export const ProductDetailsForm = withStyles(styles, {
  name: "ProductDetailsForm"
})(({ classes, data, disabled, errors, onChange }: ProductDetailsFormProps) => (
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
        initial={data.description}
        label={i18n.t("Description")}
        name="description"
        onChange={onChange}
      />
    </CardContent>
  </Card>
));
ProductDetailsForm.displayName = "ProductDetailsForm";
export default ProductDetailsForm;
