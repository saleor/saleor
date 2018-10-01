import * as React from "react";
import { Route, RouteProps } from "react-router-dom";

import { UserContext } from "..";
import AppRoot from "../../AppRoot";
import NotFound from "../../NotFound";
import { hasPermission } from "../misc";

interface SectionRouteProps extends RouteProps {
  resource?: string;
}

export const SectionRoute: React.StatelessComponent<SectionRouteProps> = ({
  resource,
  ...props
}) => (
  <UserContext.Consumer>
    {({ user }) =>
      !resource || hasPermission(resource, user) ? (
        <AppRoot>
          <Route {...props} />
        </AppRoot>
      ) : (
        <NotFound />
      )
    }
  </UserContext.Consumer>
);
SectionRoute.displayName = "Route";
export default SectionRoute;
