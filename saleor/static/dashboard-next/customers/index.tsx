import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { customerListUrl, customerUrl } from "./urls";
// import CustomerCreateView from "./views/CustomerCreate";
import CustomerDetailsViewComponent from "./views/CustomerDetails";
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

interface CustomerDetailsRouteParams {
  id: string;
}
const CustomerDetailsView: React.StatelessComponent<
  RouteComponentProps<CustomerDetailsRouteParams>
> = ({ match }) => (
  <CustomerDetailsViewComponent id={decodeURIComponent(match.params.id)} />
);

export const CustomerSection: React.StatelessComponent<{}> = () => (
  <Switch>
    <Route exact path={customerListUrl} component={CustomerListView} />
    {/* <Route exact path={customerUrl("add")} component={CustomerDetailsView} /> */}
    <Route path={customerUrl(":id")} component={CustomerDetailsView} />
  </Switch>
);
