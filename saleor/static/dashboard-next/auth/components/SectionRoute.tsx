import * as React from "react";
import { Route, RouteProps } from "react-router-dom";

import { UserContext } from "..";
import AppRoot from "../../AppRoot";
import NotFound from "../../NotFound";

interface SectionRouteProps extends RouteProps {
  resource?: string;
}

export const SectionRoute: React.StatelessComponent<SectionRouteProps> = ({
  resource,
  ...props
}) => (
  <UserContext.Consumer>
    {({ user }) =>
      resource ? (
        user.permissions.map(perm => perm.code).includes(resource) ? (
          <AppRoot>
            <Route {...props} />
          </AppRoot>
        ) : (
          <NotFound />
        )
      ) : (
        <AppRoot>
          <Route {...props} />
        </AppRoot>
      )
    }
  </UserContext.Consumer>
);
SectionRoute.displayName = "Route";
export default SectionRoute;
