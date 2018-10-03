import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import i18n from "../i18n";
import { maybe } from "../misc";
import { OrderStatus, PaymentStatusEnum } from "../types/globalTypes";
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
    case PaymentStatusEnum.CONFIRMED:
      return { localized: i18n.t("Confirmed"), status: "success" };
    case PaymentStatusEnum.REFUNDED:
      return { localized: i18n.t("Refunded"), status: "success" };
    case PaymentStatusEnum.WAITING:
      return {
        localized: i18n.t("Waiting"),
        status: "neutral"
      };
    case PaymentStatusEnum.PREAUTH:
      return { localized: i18n.t("Preauthorized"), status: "neutral" };
    case PaymentStatusEnum.INPUT:
      return { localized: i18n.t("Input"), status: "neutral" };
    case PaymentStatusEnum.REJECTED:
      return { localized: i18n.t("Rejected"), status: "error" };
    case PaymentStatusEnum.ERROR:
      return { localized: i18n.t("Error"), status: "error" };
  }
  return {
    localized: status,
    status
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
