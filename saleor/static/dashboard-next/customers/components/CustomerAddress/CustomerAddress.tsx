import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { AddressType } from "../../";
import AddressFormatter from "../../../components/AddressFormatter";
import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";

interface CustomerAddressProps {
  billingAddress: AddressType;
  shippingAddress: AddressType;
  onBillingAddressEdit?();
  onShippingAddressEdit?();
}

const decorate = withStyles(theme => ({
  hr: {
    backgroundColor: theme.palette.grey[200],
    border: "none",
    display: "block",
    height: 1,
    width: "100%"
  }
}));
const CustomerAddress = decorate<CustomerAddressProps>(
  ({
    classes,
    billingAddress,
    shippingAddress,
    onBillingAddressEdit,
    onShippingAddressEdit
  }) => (
    <Card>
      <CardTitle
        title={i18n.t("Default billing address")}
        toolbar={
          !!onBillingAddressEdit && (
            <Button
              color="secondary"
              variant="flat"
              onClick={onBillingAddressEdit}
            >
              {i18n.t("Edit address")}
            </Button>
          )
        }
      />
      <CardContent>
        <AddressFormatter address={billingAddress} />
      </CardContent>
      <hr className={classes.hr} />
      <CardTitle
        title={i18n.t("Default shipping address")}
        toolbar={
          !!onShippingAddressEdit && (
            <Button
              color="secondary"
              variant="flat"
              onClick={onShippingAddressEdit}
            >
              {i18n.t("Edit address")}
            </Button>
          )
        }
      />
      <CardContent>
        {billingAddress &&
        shippingAddress &&
        billingAddress.id === shippingAddress.id ? (
          <Typography color="textSecondary">
            {i18n.t("Same as billing address")}
          </Typography>
        ) : (
          <AddressFormatter address={shippingAddress} />
        )}
      </CardContent>
    </Card>
  )
);
export default CustomerAddress;
