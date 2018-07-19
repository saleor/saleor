import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import ControlledSwitch from "../../../components/ControlledSwitch";
import i18n from "../../../i18n";

interface ProductAvailabilityFormProps {
  data: {
    available: boolean;
    availableOn: string;
    featured: boolean;
  };
  errors: { [key: string]: string };
  loading?: boolean;
  onChange(event: any);
}

const decorate = withStyles(theme => ({
  date: {
    marginTop: theme.spacing.unit
  },
  pullDown: {
    position: "relative" as "relative",
    top: theme.spacing.unit * 1.5
  },
  pullUp: {
    marginTop: -theme.spacing.unit * 2
  }
}));
export const ProductAvailabilityForm = decorate<ProductAvailabilityFormProps>(
  ({
    classes,
    data: { available, availableOn, featured },
    errors,
    loading,
    onChange
  }) => (
    <Card>
      <CardTitle title={i18n.t("Availability")} />
      <CardContent>
        <div className={classes.pullUp}>
          <ControlledSwitch
            name="available"
            label={i18n.t("Published in storefront")}
            checked={available}
            onChange={onChange}
            disabled={loading}
          />
        </div>
        {available && (
          <>
            <TextField
              error={!!errors.availableOn}
              disabled={loading}
              label={i18n.t("Publish product on")}
              name="availableOn"
              type="date"
              fullWidth={true}
              helperText={errors.availableOn}
              value={availableOn ? availableOn : ""}
              onChange={onChange}
              className={classes.date}
              InputLabelProps={{
                shrink: true
              }}
            />
            <div className={classes.pullDown}>
              <ControlledSwitch
                name="featured"
                label={i18n.t("Feature on Homepage")}
                checked={featured}
                onChange={onChange}
                disabled={loading}
              />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
);
export default ProductAvailabilityForm;
