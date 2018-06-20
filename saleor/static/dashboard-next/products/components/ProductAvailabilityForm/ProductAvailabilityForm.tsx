import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import ControlledCheckbox from "../../../components//ControlledCheckbox";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";

interface ProductAvailabilityFormProps {
  available?: boolean;
  availableOn?: string;
  loading?: boolean;
  onChange(event: any);
}

const decorate = withStyles(theme => ({
  date: {
    marginTop: theme.spacing.unit
  },
  root: {
    display: "grid",
    gridTemplateColumns: "2fr 3fr"
  }
}));
export const ProductAvailabilityForm = decorate<ProductAvailabilityFormProps>(
  ({ classes, available, availableOn, loading, onChange }) => (
    <Card>
      <PageHeader title={i18n.t("Status")} />
      <CardContent className={classes.root}>
        <ControlledCheckbox
          name="available"
          label={i18n.t("Available on")}
          checked={available}
          onChange={onChange}
          disabled={loading}
        />
        <TextField
          disabled={!available || loading}
          name="availableOn"
          type="date"
          value={availableOn}
          onChange={onChange}
          className={classes.date}
          InputLabelProps={{
            shrink: true
          }}
        />
      </CardContent>
    </Card>
  )
);
export default ProductAvailabilityForm;
