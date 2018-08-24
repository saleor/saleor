import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import blue from "@material-ui/core/colors/blue";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface AddressType {
  city: string;
  cityArea: string;
  companyName: string;
  country: string;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: {
    prefix: string;
    number: string;
  };
  postalCode: string;
  streetAddress_1: string;
  streetAddress_2: string;
}
interface OrderCustomerProps {
  client?: {
    id: string;
    email: string;
    name: string;
  };
  shippingAddress?: AddressType;
  billingAddress?: AddressType;
  editCustomer?: boolean;
  onCustomerEditClick?();
  onCustomerEmailClick?(id: string);
  onBillingAddressEdit?();
  onShippingAddressEdit?();
}

const decorate = withStyles(
  theme => ({
    hr: {
      backgroundColor: theme.palette.grey[200],
      border: "none",
      display: "block",
      height: 1,
      width: "100%"
    },
    link: {
      color: blue[500],
      cursor: "pointer",
      textDecoration: "none"
    }
  }),
  { name: "OrderCustomer" }
);
const OrderCustomer = decorate<OrderCustomerProps>(
  ({
    classes,
    client,
    billingAddress,
    editCustomer,
    shippingAddress,
    onCustomerEditClick,
    onCustomerEmailClick,
    onBillingAddressEdit,
    onShippingAddressEdit
  }) => (
    <Card>
      <CardTitle
        title={i18n.t("Customer")}
        toolbar={
          !!editCustomer && (
            <Button
              color="secondary"
              variant="flat"
              disabled={!onCustomerEditClick}
              onClick={onCustomerEditClick}
            >
              {i18n.t("Edit")}
            </Button>
          )
        }
      />
      <CardContent>
        {client === undefined || client === null ? (
          <>
            <Skeleton />
            <Skeleton />
          </>
        ) : (
          <>
            <Typography>{client.name}</Typography>
            <Typography
              className={classes.link}
              onClick={
                onCustomerEmailClick
                  ? onCustomerEmailClick(client.id)
                  : undefined
              }
            >
              {client.email}
            </Typography>
          </>
        )}
      </CardContent>
      <hr className={classes.hr} />

      <CardTitle
        title={i18n.t("Shipping Address")}
        toolbar={
          !!editCustomer && (
            <Button
              color="secondary"
              variant="flat"
              onClick={onShippingAddressEdit}
              disabled={!onShippingAddressEdit && client === undefined}
            >
              {i18n.t("Edit")}
            </Button>
          )
        }
      />
      <CardContent>
        {client === undefined || client === null ? (
          <>
            <Skeleton />
          </>
        ) : (
          <>
            {shippingAddress.companyName && (
              <Typography>{shippingAddress.companyName}</Typography>
            )}
            <Typography>
              {shippingAddress.firstName} {shippingAddress.lastName}
            </Typography>
            <Typography>
              {shippingAddress.streetAddress_1}
              <br />
              {shippingAddress.streetAddress_2}
            </Typography>
            <Typography>
              {shippingAddress.postalCode} {shippingAddress.city}
              {shippingAddress.cityArea ? ", " + shippingAddress.cityArea : ""}
            </Typography>
            <Typography>
              {shippingAddress.countryArea
                ? shippingAddress.countryArea + ", " + shippingAddress.country
                : shippingAddress.country}
            </Typography>
          </>
        )}
      </CardContent>
      <hr className={classes.hr} />

      <CardTitle
        title={i18n.t("Billing Address")}
        toolbar={
          !!editCustomer && (
            <Button
              color="secondary"
              variant="flat"
              onClick={onBillingAddressEdit}
              disabled={!onBillingAddressEdit && client === undefined}
            >
              {i18n.t("Edit")}
            </Button>
          )
        }
      />
      <CardContent>
        {client === undefined || client === null ? (
          <>
            <Skeleton />
          </>
        ) : shippingAddress.id === billingAddress.id ? (
          <Typography>{i18n.t("Same as shipping address")}</Typography>
        ) : (
          <>
            {billingAddress.companyName && (
              <Typography>{billingAddress.companyName}</Typography>
            )}
            <Typography>
              {billingAddress.firstName} {billingAddress.lastName}
            </Typography>
            <Typography>
              {billingAddress.streetAddress_1}
              <br />
              {billingAddress.streetAddress_2}
            </Typography>
            <Typography>
              {billingAddress.postalCode} {billingAddress.city}
              {billingAddress.cityArea ? ", " + billingAddress.cityArea : ""}
            </Typography>
            <Typography>
              {billingAddress.countryArea
                ? billingAddress.countryArea + ", " + billingAddress.country
                : billingAddress.country}
            </Typography>
          </>
        )}
      </CardContent>
    </Card>
  )
);
export default OrderCustomer;
