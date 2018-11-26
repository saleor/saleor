import * as React from "react";
import { Route, RouteComponentProps } from "react-router-dom";

import SiteSettings from "./views/";

export const SiteSettingsSection: React.StatelessComponent<
  RouteComponentProps<{}>
> = ({ match }) => <Route path={match.url} component={SiteSettings} />;
export default SiteSettingsSection;
