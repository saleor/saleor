import Button from "@material-ui/core/Button";
import Dialog, { DialogProps } from "@material-ui/core/Dialog";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import DialogTitle from "@material-ui/core/DialogTitle";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import FormSpacer from "../../../components/FormSpacer";
import PhoneField from "../../../components/PhoneField";
import SingleSelectField from "../../../components/SingleSelectField";
import i18n from "../../../i18n";

interface OrderAddressEditDialogProps {
  open: boolean;
  data: {
    city: string;
    cityArea: string;
    companyName: string;
    country: string;
    countryArea: string;
    firstName: string;
    id: string;
    lastName: string;
    phone_prefix: string;
    phone_number: string;
    postalCode: string;
    streetAddress_1: string;
    streetAddress_2: string;
  };
  variant: string;
  countries?: Array<{
    code: string;
    label: string;
  }>;
  prefixes: string[];
  onChange(event: React.ChangeEvent<any>);
  onClose?();
  onConfirm?(event: React.FormEvent<any>);
}

const decorate = withStyles(
  theme => ({
    root: {
      display: "grid",
      gridColumnGap: `${theme.spacing.unit * 2}px`,
      gridTemplateColumns: "1fr 1fr"
    }
  }),
  { name: "OrderAddressEditDialog" }
);
const OrderAddressEditDialog = decorate<OrderAddressEditDialogProps>(
  ({
    children,
    classes,
    open,
    variant,
    countries,
    data,
    prefixes,
    onConfirm,
    onClose,
    onChange
  }) => (
    <Dialog open={open}>
      <DialogTitle>
        {variant === "billing"
          ? i18n.t("Edit billing address", { context: "title" })
          : i18n.t("Edit shipping address", { context: "title" })}
      </DialogTitle>
      <DialogContent>
        <div className={classes.root}>
          <div>
            <TextField
              label={i18n.t("First name")}
              name="firstName"
              onChange={onChange}
              value={data.firstName}
              fullWidth
            />
          </div>
          <div>
            <TextField
              label={i18n.t("Last name")}
              name="lastName"
              onChange={onChange}
              value={data.lastName}
              fullWidth
            />
          </div>
        </div>
        <FormSpacer />
        <TextField
          label={i18n.t("Company")}
          name="companyName"
          onChange={onChange}
          value={data.companyName}
          fullWidth
        />
        <FormSpacer />
        <TextField
          label={i18n.t("Address")}
          name="streetAddress_1"
          onChange={onChange}
          value={data.streetAddress_1}
          fullWidth
        />
        <FormSpacer />
        <TextField
          label={i18n.t("Address")}
          name="streetAddress_2"
          onChange={onChange}
          value={data.streetAddress_2}
          fullWidth
        />
        <FormSpacer />
        <TextField
          label={i18n.t("City")}
          name="city"
          onChange={onChange}
          value={data.city}
          fullWidth
        />
        <FormSpacer />
        <TextField
          label={i18n.t("City area")}
          name="cityArea"
          onChange={onChange}
          value={data.cityArea}
          fullWidth
        />
        <FormSpacer />
        <TextField
          label={i18n.t("Postal code")}
          name="postalCode"
          onChange={onChange}
          value={data.postalCode}
          fullWidth
        />
        <FormSpacer />
        <SingleSelectField
          label={i18n.t("Country")}
          name="country"
          onChange={onChange}
          value={data.country}
          choices={countries.map(c => ({ ...c, value: c.code }))}
        />
        <FormSpacer />
        <TextField
          label={i18n.t("Country area")}
          name="countryArea"
          onChange={onChange}
          value={data.countryArea}
          fullWidth
        />
        <FormSpacer />
        <PhoneField
          label={i18n.t("Phone")}
          name="phone"
          prefix={data.phone_prefix}
          number={data.phone_number}
          prefixes={prefixes}
          onChange={onChange}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          {i18n.t("Cancel", { context: "button" })}
        </Button>
        <Button color="primary" variant="raised" onClick={onConfirm}>
          {i18n.t("Confirm", { context: "button" })}
        </Button>
      </DialogActions>
    </Dialog>
  )
);
export default OrderAddressEditDialog;
