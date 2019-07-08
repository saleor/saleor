import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { createStyles, WithStyles, withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import React from "react";

import AddressEdit from "@saleor/components/AddressEdit";
import CardTitle from "@saleor/components/CardTitle";
import { FormSpacer } from "@saleor/components/FormSpacer";
import { SingleAutocompleteChoiceType } from "@saleor/components/SingleAutocompleteSelectField";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { AddressTypeInput } from "../../types";

const styles = createStyles({
  overflow: {
    overflow: "visible"
  }
});

export interface CustomerCreateAddressProps extends WithStyles<typeof styles> {
  countries: SingleAutocompleteChoiceType[];
  countryDisplayName: string;
  data: AddressTypeInput;
  disabled: boolean;
  errors: FormErrors<keyof AddressTypeInput>;
  onChange(event: React.ChangeEvent<any>);
  onCountryChange(event: React.ChangeEvent<any>);
}

const CustomerCreateAddress = withStyles(styles, {
  name: "CustomerCreateAddress"
})(
  ({
    classes,
    countries,
    countryDisplayName,
    data,
    disabled,
    errors,
    onChange,
    onCountryChange
  }: CustomerCreateAddressProps) => (
    <Card className={classes.overflow}>
      <CardTitle title={i18n.t("Primary address")} />
      <CardContent className={classes.overflow}>
        <Typography>
          {i18n.t("The primary address of this customer.")}
        </Typography>
        <FormSpacer />
        <AddressEdit
          countries={countries}
          data={data}
          disabled={disabled}
          countryDisplayValue={countryDisplayName}
          errors={errors}
          onChange={onChange}
          onCountryChange={onCountryChange}
        />
      </CardContent>
    </Card>
  )
);
CustomerCreateAddress.displayName = "CustomerCreateAddress";
export default CustomerCreateAddress;
