import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { WindowTitle } from "../components/WindowTitle";
import i18n from "../i18n";
import {
  attributeAddPath,
  attributeListPath,
  AttributeListUrlQueryParams
} from "./urls";
import AttributeListComponent from "./views/AttributeList";

const AttributeList: React.FC<RouteComponentProps<{}>> = ({ location }) => {
  const qs = parseQs(location.search.substr(1));
  const params: AttributeListUrlQueryParams = qs;
  return <AttributeListComponent params={params} />;
};

export const AttributeSection: React.FC = () => (
  <>
    <WindowTitle title={i18n.t("Attributes")} />
    <Switch>
      <Route exact path={attributeListPath} component={AttributeList} />
    </Switch>
  </>
);
export default AttributeSection;
