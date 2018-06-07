import EditIcon from "@material-ui/icons/Edit";
import Card, { CardContent } from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import { withStyles } from "material-ui/styles";
import Typography from "material-ui/Typography";
import * as React from "react";

import { AddressType } from "../../";
import AddressFormatter from "../../../components/AddressFormatter";
import PageHeader from "../../../components/PageHeader";
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
      <PageHeader title={i18n.t("Default billing address")}>
        {!!onBillingAddressEdit && (
          <IconButton onClick={onBillingAddressEdit}>
            <EditIcon />
          </IconButton>
        )}
      </PageHeader>
      <CardContent>
        <AddressFormatter address={billingAddress} />
      </CardContent>
      <hr className={classes.hr} />
      <PageHeader title={i18n.t("Default shipping address")}>
        {!!onShippingAddressEdit && (
          <IconButton onClick={onShippingAddressEdit}>
            <EditIcon />
          </IconButton>
        )}
      </PageHeader>
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
