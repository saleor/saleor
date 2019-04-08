import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import { AddressTypeInput } from "../../customers/types";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import { FormErrors } from "../../types";
import FormSpacer from "../FormSpacer";
import SingleAutocompleteSelectField from "../SingleAutocompleteSelectField";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: `${theme.spacing.unit * 2}px`,
      gridTemplateColumns: "1fr 1fr"
    }
  });

interface AddressEditProps extends WithStyles<typeof styles> {
  countries?: Array<{
    code: string;
    label: string;
  }>;
  data: AddressTypeInput;
  disabled?: boolean;
  errors: FormErrors<keyof AddressTypeInput>;
  onChange(event: React.ChangeEvent<any>);
}

const AddressEdit = withStyles(styles, { name: "AddressEdit" })(
  ({
    classes,
    countries,
    data,
    disabled,
    errors,
    onChange
  }: AddressEditProps) => (
    <>
      <div className={classes.root}>
        <div>
          <TextField
            disabled={disabled}
            error={!!errors.firstName}
            helperText={errors.firstName}
            label={i18n.t("First name")}
            name="firstName"
            onChange={onChange}
            value={data.firstName}
            fullWidth
          />
        </div>
        <div>
          <TextField
            disabled={disabled}
            error={!!errors.lastName}
            helperText={errors.lastName}
            label={i18n.t("Last name")}
            name="lastName"
            onChange={onChange}
            value={data.lastName}
            fullWidth
          />
        </div>
      </div>
      <FormSpacer />
      <div className={classes.root}>
        <div>
          <TextField
            disabled={disabled}
            error={!!errors.companyName}
            helperText={errors.companyName}
            label={i18n.t("Company")}
            name="companyName"
            onChange={onChange}
            value={data.companyName}
            fullWidth
          />
        </div>
        <div>
          <TextField
            disabled={disabled}
            error={!!errors.phone}
            fullWidth
            helperText={errors.phone}
            label={i18n.t("Phone")}
            name="phone"
            value={data.phone}
            onChange={onChange}
          />
        </div>
      </div>
      <FormSpacer />
      <TextField
        disabled={disabled}
        error={!!errors.streetAddress1}
        helperText={errors.streetAddress1}
        label={i18n.t("Address line 1")}
        name="streetAddress1"
        onChange={onChange}
        value={data.streetAddress1}
        fullWidth
      />
      <FormSpacer />
      <TextField
        disabled={disabled}
        error={!!errors.streetAddress2}
        helperText={errors.streetAddress2}
        label={i18n.t("Address line 2")}
        name="streetAddress2"
        onChange={onChange}
        value={data.streetAddress2}
        fullWidth
      />
      <FormSpacer />
      <div className={classes.root}>
        <div>
          <TextField
            disabled={disabled}
            error={!!errors.city}
            helperText={errors.city}
            label={i18n.t("City")}
            name="city"
            onChange={onChange}
            value={data.city}
            fullWidth
          />
        </div>
        <div>
          <TextField
            disabled={disabled}
            error={!!errors.postalCode}
            helperText={errors.postalCode}
            label={i18n.t("ZIP / Postal code")}
            name="postalCode"
            onChange={onChange}
            value={data.postalCode}
            fullWidth
          />
        </div>
      </div>

      <FormSpacer />
      <div className={classes.root}>
        <div>
          <SingleAutocompleteSelectField
            disabled={disabled}
            error={!!errors.country}
            helperText={errors.country}
            label={i18n.t("Country")}
            name="country"
            onChange={onChange}
            value={data.country}
            choices={maybe(
              () => countries.map(c => ({ ...c, value: c.code })),
              []
            )}
            InputProps={{
              autoComplete: "off"
            }}
          />
        </div>
        <div>
          <TextField
            disabled={disabled}
            error={!!errors.countryArea}
            helperText={errors.countryArea}
            label={i18n.t("Country area")}
            name="countryArea"
            onChange={onChange}
            value={data.countryArea}
            fullWidth
          />
        </div>
      </div>
    </>
  )
);
AddressEdit.displayName = "AddressEdit";
export default AddressEdit;
