import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import PageCreateForm from "./views/PageCreateForm";
import PageListComponent from "./views/PageList";
import PageUpdateFormComponent from "./views/PageUpdateForm";

const PageList: React.StatelessComponent<RouteComponentProps<any>> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  return <PageListComponent filters={qs} />;
};
const PageUpdateForm: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => {
  return <PageUpdateFormComponent id={match.params.id} />;
};

const Component = ({ match }) => (
  <Switch>
    <Route exact path={match.url} component={PageList} />
    <Route exact path={`${match.url}/add/`} component={PageCreateForm} />
    <Route exact path={`${match.url}/:id/`} component={PageUpdateForm} />
  </Switch>
);

export function pageEditUrl(id: string) {
  return `/pages/${id}/`;
}

export function pageStorefrontUrl(slug: string) {
  return `/page/${slug}/`;
}

export const pageListUrl = "/pages/";

export default Component;
