import { parse as parseQs } from "qs";
import React from "react";
import { Route, RouteComponentProps } from "react-router-dom";

import { siteSettingsPath, SiteSettingsUrlQueryParams } from "./urls";
import SiteSettingsComponent from "./views/";

const SiteSettings: React.FC<RouteComponentProps<{}>> = ({ location }) => {
  const qs = parseQs(location.search.substr(1));
  const params: SiteSettingsUrlQueryParams = qs;

  return <SiteSettingsComponent params={params} />;
};

export const SiteSettingsSection: React.FC = () => {
  return <Route path={siteSettingsPath} component={SiteSettings} />;
};
export default SiteSettingsSection;
