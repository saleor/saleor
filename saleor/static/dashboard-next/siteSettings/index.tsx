import * as React from "react";
import { Route, RouteComponentProps } from "react-router-dom";

import { siteSettingsPath } from "./urls";
import SiteSettings from "./views/";

export const SiteSettingsSection: React.StatelessComponent<
  RouteComponentProps<{}>
> = () => <Route path={siteSettingsPath} component={SiteSettings} />;
export default SiteSettingsSection;
