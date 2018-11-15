import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
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
  <>
    <WindowTitle title={i18n.t("Orders")} />
    <Switch>
      <Route exact path={match.url} component={OrderList} />
      <Route exact path={`${match.url}/:id/`} component={OrderDetails} />
    </Switch>
  </>
);

export const orderListUrl = "/orders/";

export const orderUrl = (id: string) => {
  return `/orders/${id}/`;
};

export default Component;
