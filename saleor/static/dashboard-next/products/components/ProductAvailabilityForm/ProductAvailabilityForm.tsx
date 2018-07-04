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
  }
}));
export const ProductAvailabilityForm = decorate<ProductAvailabilityFormProps>(
  ({ classes, available, availableOn, loading, onChange }) => (
    <Card>
      <PageHeader title={i18n.t("Status")} />
      <CardContent>
        <ControlledCheckbox
          name="available"
          label={i18n.t("Published in storefront")}
          checked={available}
          onChange={onChange}
          disabled={loading}
        />
        <TextField
          disabled={loading}
          label={i18n.t("Publish product on")}
          name="availableOn"
          type="date"
          value={availableOn ? availableOn : ""}
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
