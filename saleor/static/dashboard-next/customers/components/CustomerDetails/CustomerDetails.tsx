import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as moment from "moment-timezone";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import { ControlledCheckbox } from "../../../components/ControlledCheckbox";
import { FormSpacer } from "../../../components/FormSpacer";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { CustomerDetails_user } from "../../types/CustomerDetails";

export interface CustomerDetailsProps {
  customer: CustomerDetails_user;
  data: {
    email: string;
    isActive: boolean;
    note: string;
  };
  disabled: boolean;
  errors: {
    email?: string;
    note?: string;
  };
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles(theme => ({
  cardTitle: {
    height: 64
  },
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "1fr 1fr"
  }
}));
const CustomerDetails = decorate<CustomerDetailsProps>(
  ({ classes, customer, data, disabled, errors, onChange }) => (
    <Card>
      <CardTitle
        className={classes.cardTitle}
        title={
          <>
            {i18n.t("General Information")}
            <Typography variant="caption">
              {i18n.t("Customer since: {{ month }} {{ year }}", {
                month: moment(maybe(() => customer.dateJoined)).format("MMM"),
                year: moment(maybe(() => customer.dateJoined)).format("YYYY")
              })}
            </Typography>
          </>
        }
      />
      <CardContent>
        <ControlledCheckbox
          checked={data.isActive}
          disabled={disabled}
          label={i18n.t("User account active", {
            context: "label"
          })}
          name="isActive"
          onChange={onChange}
        />
        <FormSpacer />
        <div className={classes.root}>
          <TextField
            disabled={disabled}
            error={!!errors.email}
            fullWidth
            helperText={errors.email}
            name="email"
            type="email"
            label={i18n.t("E-mail")}
            value={data.email}
            onChange={onChange}
          />
        </div>
        <FormSpacer />
        <TextField
          disabled={disabled}
          error={!!errors.note}
          fullWidth
          multiline
          helperText={errors.note}
          name="note"
          label={i18n.t("Note")}
          value={data.note}
          onChange={onChange}
        />
      </CardContent>
    </Card>
  )
);
CustomerDetails.displayName = "CustomerDetails";
export default CustomerDetails;
