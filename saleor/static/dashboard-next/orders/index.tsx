import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { orderListUrl, orderUrl } from "./urls";
import OrderDetailsComponent from "./views/OrderDetails";
import OrderListComponent, { OrderListQueryParams } from "./views/OrderList";

const OrderList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: OrderListQueryParams = {
    after: qs.after,
    before: qs.before,
    status: qs.status
  };
  return <OrderListComponent params={params} />;
};

const OrderDetails: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => {
  return <OrderDetailsComponent id={decodeURIComponent(match.params.id)} />;
};

const Component = () => (
  <>
    <WindowTitle title={i18n.t("Orders")} />
    <Switch>
      <Route exact path={orderListUrl()} component={OrderList} />
      <Route path={orderUrl(":id")} component={OrderDetails} />
    </Switch>
  </>
);

export default Component;
