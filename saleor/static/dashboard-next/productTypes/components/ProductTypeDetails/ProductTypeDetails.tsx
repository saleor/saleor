import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";

interface ProductTypeDetailsProps {
  data?: {
    name: string;
  };
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles({
  root: {
    overflow: "visible" as "visible"
  }
});
const ProductTypeDetails = decorate<ProductTypeDetailsProps>(
  ({ classes, data, disabled, onChange }) => (
    <Card className={classes.root}>
      <CardTitle title={i18n.t("Information")} />
      <CardContent>
        <TextField
          disabled={disabled}
          fullWidth
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
