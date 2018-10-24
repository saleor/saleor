import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { customerListUrl } from "./urls";
import CustomerListViewComponent from "./views/CustomerList";

const CustomerListView: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params = {
    after: qs.after,
    before: qs.before
  };
  return <CustomerListViewComponent params={params} />;
};

export const CustomerSection: React.StatelessComponent<{}> = () => (
  <Switch>
    <Route path={customerListUrl} component={CustomerListView} />
  </Switch>
);
