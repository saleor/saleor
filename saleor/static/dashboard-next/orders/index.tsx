import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import {
  orderDraftListPath,
  OrderDraftListUrlQueryParams,
  orderListPath,
  OrderListUrlQueryParams,
  orderPath,
  OrderUrlQueryParams
} from "./urls";
import OrderDetailsComponent from "./views/OrderDetails";
import OrderDraftListComponent from "./views/OrderDraftList";
import OrderListComponent from "./views/OrderList";

const OrderList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: OrderListUrlQueryParams = qs;
  return <OrderListComponent params={params} />;
};
const OrderDraftList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: OrderDraftListUrlQueryParams = qs;
  return <OrderDraftListComponent params={params} />;
};

const OrderDetails: React.StatelessComponent<RouteComponentProps<any>> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: OrderUrlQueryParams = qs;

  return (
    <OrderDetailsComponent
      id={decodeURIComponent(match.params.id)}
      params={params}
    />
  );
};

const Component = () => (
  <>
    <WindowTitle title={i18n.t("Orders")} />
    <Switch>
      <Route exact path={orderDraftListPath} component={OrderDraftList} />
      <Route exact path={orderListPath} component={OrderList} />
      <Route path={orderPath(":id")} component={OrderDetails} />
    </Switch>
  </>
);

export default Component;
