import EditIcon from "@material-ui/icons/Edit";
import Card, { CardContent } from "material-ui/Card";
import blue from "material-ui/colors/blue";
import IconButton from "material-ui/IconButton";
import { withStyles } from "material-ui/styles";
import Typography from "material-ui/Typography";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";
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

const decorate = withStyles(theme => ({
  hr: {
    height: 1,
    display: "block",
    border: "none",
    width: "100%",
    backgroundColor: theme.palette.grey[200]
  },
  link: {
    color: blue[500],
    cursor: "pointer",
    textDecoration: "none"
  }
}));
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
      <PageHeader title={i18n.t("Customer")}>
        {editCustomer && (
          <IconButton
            disabled={!onCustomerEditClick}
            onClick={onCustomerEditClick}
          >
            <EditIcon />
          </IconButton>
        )}
      </PageHeader>
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
              className={onCustomerEmailClick ? classes.link : ""}
              onClick={
                onCustomerEmailClick
                  ? onCustomerEmailClick(client.id)
                  : () => {}
              }
            >
              {client.email}
            </Typography>
          </>
        )}
      </CardContent>
      <hr className={classes.hr} />

      <PageHeader title={i18n.t("Shipping Address")}>
        <IconButton
          onClick={onShippingAddressEdit}
          disabled={!onShippingAddressEdit && client === undefined}
        >
          <EditIcon />
        </IconButton>
      </PageHeader>
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

      <PageHeader title={i18n.t("Billing Address")}>
        <IconButton
          onClick={onShippingAddressEdit}
          disabled={!onShippingAddressEdit && client === undefined}
        >
          <EditIcon />
        </IconButton>
      </PageHeader>
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
