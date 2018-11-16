import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { staffListUrl, staffMemberDetailsUrl } from "./urls";
import StaffDetailsComponent from "./views/StaffDetails";
import StaffListComponent, { StaffListQueryParams } from "./views/StaffList";

const StaffList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: StaffListQueryParams = {
    after: qs.after,
    before: qs.before
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

const Component = () => (
  <>
    <WindowTitle title={i18n.t("Staff")} />
    <Switch>
      <Route exact path={staffListUrl} component={StaffList} />
      <Route
        exact
        path={staffMemberDetailsUrl(":id")}
        component={StaffDetails}
      />
    </Switch>
  </>
);

export default Component;
