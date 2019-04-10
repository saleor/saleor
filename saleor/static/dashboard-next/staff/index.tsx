import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import {
  staffListPath,
  StaffListUrlQueryParams,
  staffMemberDetailsPath,
  StaffMemberDetailsUrlQueryParams
} from "./urls";
import StaffDetailsComponent from "./views/StaffDetails";
import StaffListComponent from "./views/StaffList";

const StaffList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: StaffListUrlQueryParams = qs;
  return <StaffListComponent params={params} />;
};

interface StaffDetailsRouteProps {
  id: string;
}
const StaffDetails: React.StatelessComponent<
  RouteComponentProps<StaffDetailsRouteProps>
> = ({ match }) => {
  const qs = parseQs(location.search.substr(1));
  const params: StaffMemberDetailsUrlQueryParams = qs;

  return (
    <StaffDetailsComponent
      id={decodeURIComponent(match.params.id)}
      params={params}
    />
  );
};

const Component = () => (
  <>
    <WindowTitle title={i18n.t("Staff")} />
    <Switch>
      <Route exact path={staffListPath} component={StaffList} />
      <Route path={staffMemberDetailsPath(":id")} component={StaffDetails} />
    </Switch>
  </>
);

export default Component;
