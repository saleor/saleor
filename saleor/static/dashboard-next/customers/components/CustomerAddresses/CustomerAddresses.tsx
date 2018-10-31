import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import AddressFormatter from "../../../components/AddressFormatter/AddressFormatter";
import CardTitle from "../../../components/CardTitle";
import { Hr } from "../../../components/Hr";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { CustomerDetails_user } from "../../types/CustomerDetails";

export interface CustomerAddressesProps {
  customer: CustomerDetails_user;
  disabled: boolean;
  onAddressManageClick: () => void;
}

const decorate = withStyles(theme => ({
  label: {
    fontWeight: 600 as 600,
    marginBottom: theme.spacing.unit
  }
}));
const CustomerAddresses = decorate<CustomerAddressesProps>(
  ({ classes, customer }) => (
    <Card>
      <CardTitle
        title={i18n.t("Address Information")}
        // toolbar={ // TODO: add address management #3173
        //   <Button
        //     color="secondary"
        //     disabled={disabled}
        //     variant="flat"
        //     onClick={onAddressManageClick}
        //   >
        //     {i18n.t("Manage", { context: "button" })}
        //   </Button>
        // }
      />
      {customer &&
      customer.defaultBillingAddress &&
      customer.defaultBillingAddress.id &&
      customer.defaultShippingAddress &&
      customer.defaultShippingAddress.id &&
      customer.defaultBillingAddress.id !==
        customer.defaultShippingAddress.id ? (
        <>
          <CardContent>
            <Typography className={classes.label}>
              {i18n.t("Billing address")}
            </Typography>
            <AddressFormatter
              address={maybe(() => customer.defaultBillingAddress)}
            />
          </CardContent>
          <Hr />
          <CardContent>
            <Typography className={classes.label}>
              {i18n.t("Shipping address")}
            </Typography>
            <AddressFormatter
              address={maybe(() => customer.defaultShippingAddress)}
            />
          </CardContent>
        </>
      ) : (
        <CardContent>
          <Typography className={classes.label}>{i18n.t("Address")}</Typography>
          <AddressFormatter
            address={maybe(() => customer.defaultBillingAddress)}
          />
        </CardContent>
      )}
    </Card>
  )
);
CustomerAddresses.displayName = "CustomerAddresses";
export default CustomerAddresses;
