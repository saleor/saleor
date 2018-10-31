import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { collectionAddUrl, collectionListUrl, collectionUrl } from "./urls";
import CollectionCreate from "./views/CollectionCreate";
import CollectionDetailsView from "./views/CollectionDetails";
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

interface CollectionDetailsRouteProps {
  id: string;
}
const CollectionDetails: React.StatelessComponent<
  RouteComponentProps<CollectionDetailsRouteProps>
> = ({ location, match }) => {
  const qs = parseQs(location.search.substr(1));
  const params = {
    after: qs.after,
    before: qs.before
  };
  return (
    <CollectionDetailsView
      id={decodeURIComponent(match.params.id)}
      params={params}
    />
  );
};

const Component = () => (
  <Switch>
    <Route exact path={collectionListUrl} component={CollectionList} />
    <Route exact path={collectionAddUrl} component={CollectionCreate} />
    <Route path={collectionUrl(":id")} component={CollectionDetails} />
  </Switch>
);
export default Component;
