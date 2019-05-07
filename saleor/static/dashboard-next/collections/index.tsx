import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import {
  collectionAddPath,
  collectionListPath,
  CollectionListUrlQueryParams,
  collectionPath,
  CollectionUrlQueryParams
} from "./urls";
import CollectionCreate from "./views/CollectionCreate";
import CollectionDetailsView from "./views/CollectionDetails";
import CollectionListView from "./views/CollectionList";

const CollectionList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: CollectionListUrlQueryParams = qs;
  return <CollectionListView params={params} />;
};

interface CollectionDetailsRouteProps {
  id: string;
}
const CollectionDetails: React.StatelessComponent<
  RouteComponentProps<CollectionDetailsRouteProps>
> = ({ location, match }) => {
  const qs = parseQs(location.search.substr(1));
  const params: CollectionUrlQueryParams = qs;
  return (
    <CollectionDetailsView
      id={decodeURIComponent(match.params.id)}
      params={params}
    />
  );
};

const Component = () => (
  <>
    <WindowTitle title={i18n.t("Collections")} />
    <Switch>
      <Route exact path={collectionListPath} component={CollectionList} />
      <Route exact path={collectionAddPath} component={CollectionCreate} />
      <Route path={collectionPath(":id")} component={CollectionDetails} />
    </Switch>
  </>
);
export default Component;
