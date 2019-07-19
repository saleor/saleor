import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import React from "react";

import CardTitle from "@saleor/components/CardTitle";
import FormSpacer from "@saleor/components/FormSpacer";
import Grid from "@saleor/components/Grid";
import SingleAutocompleteSelectField, {
  SingleAutocompleteChoiceType
} from "@saleor/components/SingleAutocompleteSelectField";
import { AddressTypeInput } from "@saleor/customers/types";
import { ChangeEvent } from "@saleor/hooks/useForm";
import i18n from "@saleor/i18n";
import { FormErrors } from "@saleor/types";
import { SiteSettingsPageFormData } from "../SiteSettingsPage";

interface SiteSettingsAddressProps extends WithStyles<typeof styles> {
  countries: SingleAutocompleteChoiceType[];
  data: SiteSettingsPageFormData;
  displayCountry: string;
  errors: FormErrors<keyof AddressTypeInput>;
  disabled: boolean;
  onChange: (event: ChangeEvent) => void;
  onCountryChange: (event: ChangeEvent) => void;
}

const styles = createStyles({
  root: {
    overflow: "visible"
  }
});

const SiteSettingsAddress = withStyles(styles, { name: "SiteSettingsAddress" })(
  ({
    classes,
    countries,
    data,
    disabled,
    displayCountry,
    errors,
    onChange,
    onCountryChange
  }: SiteSettingsAddressProps) => (
    <Card className={classes.root}>
      <CardTitle
        title={i18n.t("Store information", {
          context: "store configuration"
        })}
      />
      <CardContent>
        <TextField
          disabled={disabled}
          error={!!errors.companyName}
          helperText={errors.companyName}
          label={i18n.t("Company")}
          name={"companyName" as keyof SiteSettingsPageFormData}
          onChange={onChange}
          value={data.companyName}
          fullWidth
        />
        <FormSpacer />
        <TextField
          disabled={disabled}
          error={!!errors.streetAddress1}
          helperText={errors.streetAddress1}
          label={i18n.t("Address line 1")}
          name={"streetAddress1" as keyof SiteSettingsPageFormData}
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
          name={"streetAddress2" as keyof SiteSettingsPageFormData}
          onChange={onChange}
          value={data.streetAddress2}
          fullWidth
        />
        <FormSpacer />
        <Grid>
          <TextField
            disabled={disabled}
            error={!!errors.city}
            helperText={errors.city}
            label={i18n.t("City")}
            name={"city" as keyof SiteSettingsPageFormData}
            onChange={onChange}
            value={data.city}
            fullWidth
          />
          <TextField
            disabled={disabled}
            error={!!errors.postalCode}
            helperText={errors.postalCode}
            label={i18n.t("ZIP / Postal code")}
            name={"postalCode" as keyof SiteSettingsPageFormData}
            onChange={onChange}
            value={data.postalCode}
            fullWidth
          />
        </Grid>
        <FormSpacer />
        <Grid>
          <SingleAutocompleteSelectField
            disabled={disabled}
            displayValue={displayCountry}
            error={!!errors.country}
            helperText={errors.country}
            label={i18n.t("Country")}
            name={"country" as keyof SiteSettingsPageFormData}
            onChange={onCountryChange}
            value={data.country}
            choices={countries}
            InputProps={{
              autoComplete: "off"
            }}
          />
          <TextField
            disabled={disabled}
            error={!!errors.countryArea}
            helperText={errors.countryArea}
            label={i18n.t("Country area")}
            name={"countryArea" as keyof SiteSettingsPageFormData}
            onChange={onChange}
            value={data.countryArea}
            fullWidth
          />
        </Grid>
        <FormSpacer />
        <TextField
          disabled={disabled}
          error={!!errors.phone}
          fullWidth
          helperText={errors.phone}
          label={i18n.t("Phone")}
          name={"phone" as keyof SiteSettingsPageFormData}
          value={data.phone}
          onChange={onChange}
        />
      </CardContent>
    </Card>
  )
);
SiteSettingsAddress.displayName = "SiteSettingsAddress";
export default SiteSettingsAddress;
