import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import AddressEdit from "../../../components/AddressEdit/AddressEdit";
import CardTitle from "../../../components/CardTitle";
import { FormSpacer } from "../../../components/FormSpacer";
import i18n from "../../../i18n";
import { AddressTypeInput } from "../../types";
import { CustomerCreateData_shop_countries } from "../../types/CustomerCreateData";

export interface CustomerCreateAddressProps {
  countries: CustomerCreateData_shop_countries[];
  data: AddressTypeInput;
  disabled: boolean;
  errors: { [T in keyof AddressTypeInput]?: string };
  onChange(event: React.ChangeEvent<any>);
}

const CustomerCreateAddress: React.StatelessComponent<
  CustomerCreateAddressProps
> = ({ countries, data, disabled, errors, onChange }) => (
  <Card>
    <CardTitle title={i18n.t("Primary address")} />
    <CardContent>
      <Typography>{i18n.t("The primary address of this customer.")}</Typography>
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
);
CustomerCreateAddress.displayName = "CustomerCreateAddress";
export default CustomerCreateAddress;
