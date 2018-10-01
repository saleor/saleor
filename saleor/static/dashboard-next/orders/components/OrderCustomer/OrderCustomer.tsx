import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import ExternalLink from "../../../components/ExternalLink";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface AddressType {
  city: string;
  cityArea: string;
  companyName: string;
  country: {
    code: string;
    country: string;
  };
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}
export interface OrderCustomerProps {
  customer: {
    id: string;
    email: string;
  };
  shippingAddress?: AddressType;
  billingAddress?: AddressType;
  canEditCustomer?: boolean;
  onCustomerEditClick?();
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
    }
  }),
  { name: "OrderCustomer" }
);
const OrderCustomer = decorate<OrderCustomerProps>(
  ({
    classes,
    customer,
    billingAddress,
    canEditCustomer,
    shippingAddress,
    onCustomerEditClick,
    onBillingAddressEdit,
    onShippingAddressEdit
  }) => (
    <Card>
      <CardTitle
        title={i18n.t("Customer")}
        toolbar={
          !!canEditCustomer && (
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
        {customer === undefined ? (
          <>
            <Skeleton />
            <Skeleton />
          </>
        ) : customer === null ? (
          <Typography>{i18n.t("Anonymous customer")}</Typography>
        ) : (
          <ExternalLink href={`mailto:${customer.email}`}>
            {customer.email}
          </ExternalLink>
        )}
      </CardContent>
      <hr className={classes.hr} />

      <CardTitle
        title={i18n.t("Shipping Address")}
        toolbar={
          <Button
            color="secondary"
            variant="flat"
            onClick={onShippingAddressEdit}
            disabled={!onShippingAddressEdit && customer === undefined}
          >
            {i18n.t("Edit")}
          </Button>
        }
      />
      <CardContent>
        {shippingAddress === undefined ? (
          <Skeleton />
        ) : shippingAddress === null ? (
          <Typography>{i18n.t("Not set")}</Typography>
        ) : (
          <>
            {shippingAddress.companyName && (
              <Typography>{shippingAddress.companyName}</Typography>
            )}
            <Typography>
              {shippingAddress.firstName} {shippingAddress.lastName}
            </Typography>
            <Typography>
              {shippingAddress.streetAddress1}
              <br />
              {shippingAddress.streetAddress2}
            </Typography>
            <Typography>
              {shippingAddress.postalCode} {shippingAddress.city}
              {shippingAddress.cityArea ? ", " + shippingAddress.cityArea : ""}
            </Typography>
            <Typography>
              {shippingAddress.countryArea
                ? shippingAddress.countryArea +
                  ", " +
                  shippingAddress.country.country
                : shippingAddress.country.country}
            </Typography>
          </>
        )}
      </CardContent>
      <hr className={classes.hr} />

      <CardTitle
        title={i18n.t("Billing Address")}
        toolbar={
          <Button
            color="secondary"
            variant="flat"
            onClick={onBillingAddressEdit}
            disabled={!onBillingAddressEdit && customer === undefined}
          >
            {i18n.t("Edit")}
          </Button>
        }
      />
      <CardContent>
        {billingAddress === undefined ? (
          <Skeleton />
        ) : billingAddress === null ? (
          <Typography>{i18n.t("Not set")}</Typography>
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
              {billingAddress.streetAddress1}
              <br />
              {billingAddress.streetAddress2}
            </Typography>
            <Typography>
              {billingAddress.postalCode} {billingAddress.city}
              {billingAddress.cityArea ? ", " + billingAddress.cityArea : ""}
            </Typography>
            <Typography>
              {billingAddress.countryArea
                ? billingAddress.countryArea +
                  ", " +
                  billingAddress.country.country
                : billingAddress.country.country}
            </Typography>
          </>
        )}
      </CardContent>
    </Card>
  )
);
export default OrderCustomer;
