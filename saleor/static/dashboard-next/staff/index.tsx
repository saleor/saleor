import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import StaffDetailsComponent from "./views/StaffDetails";
import StaffListComponent from "./views/StaffList";

const StaffList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params = {
    after: decodeURIComponent(qs.after),
    before: decodeURIComponent(qs.before)
  };
  return <StaffListComponent params={params} />;
};

interface StaffDetailsRouteProps {
  id: string;
}
const StaffDetails: React.StatelessComponent<
  RouteComponentProps<StaffDetailsRouteProps>
> = ({ match }) => (
  <StaffDetailsComponent id={decodeURIComponent(match.params.id)} />
);

const Component = ({ match }) => (
  <Switch>
    <Route exact path={match.url} component={StaffList} />
    <Route exact path={`${match.url}/:id/`} component={StaffDetails} />
  </Switch>
);

export const staffListUrl = "/staff/";
export const staffMemberDetailsUrl = (id: string) => {
  return `/staff/${id}/`;
};

export default Component;
