import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { collectionListUrl } from "./urls";
import CollectionListView from "./views/CollectionList";

const CollectionList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params = {
    after: qs.after,
    before: qs.before
  };
  return <CollectionListView params={params} />;
};

const Component = () => (
  <Switch>
    <Route exact path={collectionListUrl} component={CollectionList} />
    {/* <Route exact path={`${match.url}/add/`} component={CategoryCreate} />
    <Route exact path={`${match.url}/:id/add/`} component={CategoryCreate} />
    <Route path={`${match.url}/:id/`} component={CategoryDetails} /> */}
  </Switch>
);
export default Component;
