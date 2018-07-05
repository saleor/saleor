import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import ControlledCheckbox from "../../../components//ControlledCheckbox";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";

interface ProductAvailabilityFormProps {
  data: {
    available: boolean;
    availableOn: string;
    chargeTaxes: boolean;
    featured: boolean;
  };
  loading?: boolean;
  onChange(event: any);
}

const decorate = withStyles(theme => ({
  date: {
    marginTop: theme.spacing.unit
  }
}));
export const ProductAvailabilityForm = decorate<ProductAvailabilityFormProps>(
  ({
    classes,
    data: { available, availableOn, chargeTaxes, featured },
    loading,
    onChange
  }) => (
    <Card>
      <PageHeader title={i18n.t("Status")} />
      <CardContent>
        <div>
          <ControlledCheckbox
            name="available"
            label={i18n.t("Published in storefront")}
            checked={available}
            onChange={onChange}
            disabled={loading}
          />
        </div>
        {available && (
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
        )}
        <div>
          <ControlledCheckbox
            name="featured"
            label={i18n.t("Feature this product on homepage")}
            checked={featured}
            onChange={onChange}
            disabled={loading}
          />
        </div>
        <div>
          <ControlledCheckbox
            name="chargeTaxes"
            label={i18n.t("Charge taxes")}
            checked={chargeTaxes}
            onChange={onChange}
            disabled={loading}
          />
        </div>
      </CardContent>
    </Card>
  )
);
export default ProductAvailabilityForm;
