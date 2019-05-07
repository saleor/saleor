import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { createStyles, WithStyles, withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import AddressEdit from "../../../components/AddressEdit/AddressEdit";
import CardTitle from "../../../components/CardTitle";
import { FormSpacer } from "../../../components/FormSpacer";
import i18n from "../../../i18n";
import { FormErrors } from "../../../types";
import { AddressTypeInput } from "../../types";
import { CustomerCreateData_shop_countries } from "../../types/CustomerCreateData";

const styles = createStyles({
  overflow: {
    overflow: "visible"
  }
});

export interface CustomerCreateAddressProps extends WithStyles<typeof styles> {
  countries: CustomerCreateData_shop_countries[];
  data: AddressTypeInput;
  disabled: boolean;
  errors: FormErrors<keyof AddressTypeInput>;
  onChange(event: React.ChangeEvent<any>);
}

const CustomerCreateAddress = withStyles(styles, {
  name: "CustomerCreateAddress"
})(
  ({
    classes,
    countries,
    data,
    disabled,
    errors,
    onChange
  }: CustomerCreateAddressProps) => (
    <Card className={classes.overflow}>
      <CardTitle title={i18n.t("Primary address")} />
      <CardContent className={classes.overflow}>
        <Typography>
          {i18n.t("The primary address of this customer.")}
        </Typography>
        <FormSpacer />
        <AddressEdit
          countries={countries.map(country => ({
            code: country.code,
            label: country.country
          }))}
          data={data}
          disabled={disabled}
          errors={errors}
          onChange={onChange}
        />
      </CardContent>
    </Card>
  )
);
CustomerCreateAddress.displayName = "CustomerCreateAddress";
export default CustomerCreateAddress;
