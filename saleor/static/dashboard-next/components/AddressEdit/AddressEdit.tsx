import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import { AddressTypeInput } from "../../customers/";
import i18n from "../../i18n";
import FormSpacer from "../FormSpacer";
import PhoneField from "../PhoneField";
import SingleSelectField from "../SingleSelectField";

interface AddressEditProps {
  countries?: Array<{
    code: string;
    label: string;
  }>;
  data: AddressTypeInput;
  prefixes: string[];
  onChange(event: React.ChangeEvent<any>);
}

const decorate = withStyles(theme => ({
  root: {
    display: "grid",
    gridColumnGap: `${theme.spacing.unit * 2}px`,
    gridTemplateColumns: "1fr 1fr"
  }
}));
const AddressEdit = decorate<AddressEditProps>(
  ({ classes, countries, data, prefixes, onChange }) => (
    <>
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
    </>
  )
);
export default AddressEdit;
