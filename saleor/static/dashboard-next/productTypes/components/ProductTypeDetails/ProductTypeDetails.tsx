import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import i18n from "@saleor/i18n";
import { FormErrors } from "@saleor/types";

const styles = createStyles({
  root: {
    overflow: "visible"
  }
});

interface ProductTypeDetailsProps extends WithStyles<typeof styles> {
  data?: {
    name: string;
  };
  disabled: boolean;
  errors: FormErrors<"name">;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const ProductTypeDetails = withStyles(styles, { name: "ProductTypeDetails" })(
  ({ classes, data, disabled, errors, onChange }: ProductTypeDetailsProps) => (
    <Card className={classes.root}>
      <CardTitle title={i18n.t("Information")} />
      <CardContent>
        <TextField
          disabled={disabled}
          error={!!errors.name}
          fullWidth
          helperText={errors.name}
          label={i18n.t("Product Type Name")}
          name="name"
          onChange={onChange}
          value={data.name}
        />
      </CardContent>
    </Card>
  )
);
ProductTypeDetails.displayName = "ProductTypeDetails";
export default ProductTypeDetails;
