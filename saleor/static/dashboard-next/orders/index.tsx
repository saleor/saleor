import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import i18n from "../i18n";
import { FulfillmentStatus, OrderStatus } from "../types/globalTypes";
import OrderDetailsComponent from "./views/OrderDetails";
import OrderListComponent from "./views/OrderList";

const OrderList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params = {
    after: qs.after,
    before: qs.before
  };
  return <OrderListComponent params={params} />;
};

const OrderDetails: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => {
  return <OrderDetailsComponent id={match.params.id} />;
};

const Component = ({ match }) => (
  <Switch>
    <Route exact path={match.url} component={OrderList} />
    <Route exact path={`${match.url}/:id/`} component={OrderDetails} />
  </Switch>
);

export interface AddressType {
  city: string;
  cityArea: string;
  companyName: string;
  country: string;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export const PaymentStatus = {
  CONFIRMED: "confirmed",
  ERROR: "error",
  INPUT: "input",
  PREAUTH: "preauth",
  REFUNDED: "refunded",
  REJECTED: "rejected",
  WAITING: "waiting"
};
export const PaymentVariants = {
  MANUAL: "manual"
};

export const transformPaymentStatus = (status: string) => {
  switch (status) {
    case PaymentStatus.CONFIRMED:
      return { localized: i18n.t("Confirmed"), status: "success" };
    case PaymentStatus.REFUNDED:
      return { localized: i18n.t("Refunded"), status: "success" };
    case PaymentStatus.WAITING:
      return {
        localized: i18n.t("Waiting for confirmation"),
        status: "neutral"
      };
    case PaymentStatus.PREAUTH:
      return { localized: i18n.t("Preauthorized"), status: "neutral" };
    case PaymentStatus.INPUT:
      return { localized: i18n.t("Input"), status: "neutral" };
    case PaymentStatus.REJECTED:
      return { localized: i18n.t("Rejected"), status: "error" };
    case PaymentStatus.ERROR:
      return { localized: i18n.t("Error"), status: "error" };
  }
  return {
    localized: status,
    status: "error"
  };
};

export const transformOrderStatus = (status: string) => {
  switch (status) {
    case OrderStatus.FULFILLED:
      return { localized: i18n.t("Fulfilled"), status: "success" };
    case OrderStatus.PARTIALLY_FULFILLED:
      return { localized: i18n.t("Partially fulfilled"), status: "neutral" };
    case OrderStatus.UNFULFILLED:
      return { localized: i18n.t("Unfulfilled"), status: "error" };
    case OrderStatus.CANCELED:
      return { localized: i18n.t("Cancelled"), status: "error" };
    case OrderStatus.DRAFT:
      return { localized: i18n.t("Draft"), status: "error" };
  }
  return {
    localized: status,
    status: "error"
  };
};

export const transformFulfillmentStatus = (status: string) => {
  switch (status) {
    case FulfillmentStatus.FULFILLED:
      return { localized: i18n.t("Fulfilled"), status: "success" };
    case FulfillmentStatus.CANCELED:
      return { localized: i18n.t("Cancelled"), status: "neutral" };
  }
  return {
    localized: status,
    status: "error"
  };
};

export const transformAddressToForm = (data: AddressType) => ({
  ...data,
  phone: data.phone
});

export const orderListUrl = "/orders/";

export const orderUrl = (id: string) => {
  return `/orders/${id}/`;
};

export default Component;
