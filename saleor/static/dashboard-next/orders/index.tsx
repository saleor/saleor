import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import i18n from "../i18n";
import { maybe } from "../misc";
import { OrderStatus, PaymentChargeStatusEnum } from "../types/globalTypes";
import OrderDetailsComponent from "./views/OrderDetails";
import OrderListComponent, { OrderListQueryParams } from "./views/OrderList";

const OrderList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: OrderListQueryParams = {
    after: qs.after,
    before: qs.before
  };
  return <OrderListComponent params={params} />;
};

const OrderDetails: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => {
  return <OrderDetailsComponent id={decodeURIComponent(match.params.id)} />;
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

export const transformPaymentStatus = (status: string) => {
  switch (status) {
    case PaymentChargeStatusEnum.CHARGED:
      return { localized: i18n.t("Paid"), status: "success" };
    case PaymentChargeStatusEnum.FULLY_REFUNDED:
      return { localized: i18n.t("Refunded"), status: "success" };
    default:
      return { localized: i18n.t("Unpaid"), status: "error" };
  }
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

export const transformAddressToForm = (data: AddressType) => ({
  city: maybe(() => data.city, ""),
  cityArea: maybe(() => data.cityArea, ""),
  companyName: maybe(() => data.companyName, ""),
  country: maybe(() => data.country.code, ""),
  countryArea: maybe(() => data.countryArea, ""),
  firstName: maybe(() => data.firstName, ""),
  lastName: maybe(() => data.lastName, ""),
  phone: maybe(() => data.phone, ""),
  postalCode: maybe(() => data.postalCode, ""),
  streetAddress1: maybe(() => data.streetAddress1, ""),
  streetAddress2: maybe(() => data.streetAddress2, "")
});

export const orderListUrl = "/orders/";

export const orderUrl = (id: string) => {
  return `/orders/${id}/`;
};

export default Component;
