import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as moment from "moment-timezone";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import { ControlledCheckbox } from "../../../components/ControlledCheckbox";
import { FormSpacer } from "../../../components/FormSpacer";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { CustomerDetails_user } from "../../types/CustomerDetails";

const styles = (theme: Theme) =>
  createStyles({
    cardTitle: {
      height: 64
    },
    root: {
      display: "grid" as "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridRowGap: theme.spacing.unit * 3 + "px",
      gridTemplateColumns: "1fr 1fr"
    }
  });

export interface CustomerDetailsProps extends WithStyles<typeof styles> {
  customer: CustomerDetails_user;
  data: {
    firstName: string;
    lastName: string;
    email: string;
    isActive: boolean;
    note: string;
  };
  disabled: boolean;
  errors: {
    firstName?: string;
    lastName?: string;
    email?: string;
    note?: string;
  };
  onChange: (event: React.ChangeEvent<any>) => void;
}

const CustomerDetails = withStyles(styles, { name: "CustomerDetails" })(
  ({
    classes,
    customer,
    data,
    disabled,
    errors,
    onChange
  }: CustomerDetailsProps) => (
    <Card>
      <CardTitle
        className={classes.cardTitle}
        title={
          <>
            {i18n.t("General Information")}
            {customer && customer.dateJoined ? (
              <Typography variant="caption">
                {i18n.t("Customer since: {{ month }} {{ year }}", {
                  month: moment(customer.dateJoined).format("MMM"),
                  year: moment(customer.dateJoined).format("YYYY")
                })}
              </Typography>
            ) : (
              <Skeleton style={{ width: "10rem" }} />
            )}
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
            error={!!errors.firstName}
            fullWidth
            helperText={errors.firstName}
            name="firstName"
            type="text"
            label={i18n.t("First Name")}
            value={data.firstName}
            onChange={onChange}
          />
          <TextField
            disabled={disabled}
            error={!!errors.lastName}
            fullWidth
            helperText={errors.lastName}
            name="lastName"
            type="text"
            label={i18n.t("Last Name")}
            value={data.lastName}
            onChange={onChange}
          />
        </div>
        <FormSpacer />
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
