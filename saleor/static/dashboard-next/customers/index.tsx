import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { customerAddPath, customerListPath, customerPath } from "./urls";
import CustomerCreateView from "./views/CustomerCreate";
import CustomerDetailsViewComponent from "./views/CustomerDetails";
import CustomerListViewComponent, {
  CustomerListQueryParams
} from "./views/CustomerList";

const CustomerListView: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: CustomerListQueryParams = {
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
  <>
    <WindowTitle title={i18n.t("Customers")} />
    <Switch>
      <Route exact path={customerListPath} component={CustomerListView} />
      <Route exact path={customerAddPath} component={CustomerCreateView} />
      <Route path={customerPath(":id")} component={CustomerDetailsView} />
    </Switch>
  </>
);
