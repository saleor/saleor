import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import {
  pageCreatePath,
  pageListPath,
  PageListUrlQueryParams,
  pagePath,
  PageUrlQueryParams
} from "./urls";
import PageCreate from "./views/PageCreate";
import PageDetailsComponent from "./views/PageDetails";
import PageListComponent from "./views/PageList";

const PageList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: PageListUrlQueryParams = qs;
  return <PageListComponent params={params} />;
};

const PageDetails: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: PageUrlQueryParams = qs;

  return (
    <PageDetailsComponent
      id={decodeURIComponent(match.params.id)}
      params={params}
    />
  );
};

const Component = () => (
  <>
    <WindowTitle title={i18n.t("Pages")} />
    <Switch>
      <Route exact path={pageListPath} component={PageList} />
      <Route exact path={pageCreatePath} component={PageCreate} />
      <Route path={pagePath(":id")} component={PageDetails} />
    </Switch>
  </>
);

export default Component;
