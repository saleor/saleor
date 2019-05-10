import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import {
  customerAddPath,
  customerAddressesPath,
  CustomerAddressesUrlQueryParams,
  customerListPath,
  CustomerListUrlQueryParams,
  customerPath,
  CustomerUrlQueryParams
} from "./urls";
import CustomerAddressesViewComponent from "./views/CustomerAddresses";
import CustomerCreateView from "./views/CustomerCreate";
import CustomerDetailsViewComponent from "./views/CustomerDetails";
import CustomerListViewComponent from "./views/CustomerList";

const CustomerListView: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: CustomerListUrlQueryParams = qs;
  return <CustomerListViewComponent params={params} />;
};

interface CustomerDetailsRouteParams {
  id: string;
}
const CustomerDetailsView: React.StatelessComponent<
  RouteComponentProps<CustomerDetailsRouteParams>
> = ({ location, match }) => {
  const qs = parseQs(location.search.substr(1));
  const params: CustomerUrlQueryParams = qs;

  return (
    <CustomerDetailsViewComponent
      id={decodeURIComponent(match.params.id)}
      params={params}
    />
  );
};

interface CustomerAddressesRouteParams {
  id: string;
}
const CustomerAddressesView: React.StatelessComponent<
  RouteComponentProps<CustomerAddressesRouteParams>
> = ({ match }) => {
  const qs = parseQs(location.search.substr(1));
  const params: CustomerAddressesUrlQueryParams = qs;

  return (
    <CustomerAddressesViewComponent
      id={decodeURIComponent(match.params.id)}
      params={params}
    />
  );
};

export const CustomerSection: React.StatelessComponent<{}> = () => (
  <>
    <WindowTitle title={i18n.t("Customers")} />
    <Switch>
      <Route exact path={customerListPath} component={CustomerListView} />
      <Route exact path={customerAddPath} component={CustomerCreateView} />
      <Route
        path={customerAddressesPath(":id")}
        component={CustomerAddressesView}
      />
      <Route path={customerPath(":id")} component={CustomerDetailsView} />
    </Switch>
  </>
);
