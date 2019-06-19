import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import {
  attributeAddPath,
  AttributeAddUrlQueryParams,
  attributeListPath,
  AttributeListUrlQueryParams,
  attributePath,
  AttributeUrlQueryParams
} from "./urls";
import AttributeCreateComponent from "./views/AttributeCreate";
import AttributeDetailsComponent from "./views/AttributeDetails";
import AttributeListComponent from "./views/AttributeList";

const AttributeList: React.FC<RouteComponentProps<{}>> = ({ location }) => {
  const qs = parseQs(location.search.substr(1));
  const params: AttributeListUrlQueryParams = qs;
  return <AttributeListComponent params={params} />;
};

const AttributeCreate: React.FC<RouteComponentProps<{}>> = ({ location }) => {
  const qs = parseQs(location.search.substr(1));
  const params: AttributeAddUrlQueryParams = qs;
  return <AttributeCreateComponent params={params} />;
};

const AttributeDetails: React.FC<RouteComponentProps<{ id: string }>> = ({
  location,
  match
}) => {
  const qs = parseQs(location.search.substr(1));
  const params: AttributeUrlQueryParams = qs;
  return <AttributeDetailsComponent id={match.params.id} params={params} />;
};

export const AttributeSection: React.FC = () => (
  <>
    <WindowTitle title={i18n.t("Attributes")} />
    <Switch>
      <Route exact path={attributeListPath} component={AttributeList} />
      <Route exact path={attributeAddPath} component={AttributeCreate} />
      <Route path={attributePath(":id")} component={AttributeDetails} />
    </Switch>
  </>
);
export default AttributeSection;
