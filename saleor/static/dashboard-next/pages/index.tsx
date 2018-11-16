import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import { pageAddUrl, pageListUrl, pageUrl } from "./urls";
import PageCreate from "./views/PageCreate";
import PageDetailsComponent from "./views/PageDetails";
import PageListComponent, { PageListQueryParams } from "./views/PageList";

const PageList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: PageListQueryParams = {
    after: qs.after,
    before: qs.before
  };
  return <PageListComponent params={params} />;
};
const PageDetails: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => {
  return <PageDetailsComponent id={match.params.id} />;
};

const Component = () => (
  <>
    <WindowTitle title={i18n.t("Pages")} />
    <Switch>
      <Route exact path={pageListUrl} component={PageList} />
      <Route exact path={pageAddUrl} component={PageCreate} />
      <Route exact path={pageUrl(":id")} component={PageDetails} />
    </Switch>
  </>
);

export default Component;
