import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import StaffListComponent from "./views/StaffList";

const StaffList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params = {
    after: qs.after,
    before: qs.before
  };
  return <StaffListComponent params={params} />;
};

const Component = ({ match }) => (
  <Switch>
    <Route exact path={match.url} component={StaffList} />
  </Switch>
);

export const staffListUrl = "/staff/";

export const staffMemberDetailsUrl = (id: string) => {
  return `/staff/${id}/`;
};

export default Component;
