import * as React from "react";
import { Route, RouteProps } from "react-router-dom";

import { UserContext } from "..";
import AppRoot from "../../AppRoot";
import NotFound from "../../NotFound";
import { PermissionEnum } from '../../types/globalTypes';
import { hasPermission } from "../misc";

interface SectionRouteProps extends RouteProps {
  permissions?: PermissionEnum[];
}

export const SectionRoute: React.StatelessComponent<SectionRouteProps> = ({
  permissions,
  ...props
}) => (
  <UserContext.Consumer>
    {({ user }) =>
      !permissions ||
      permissions
        .map(permission => hasPermission(permission, user))
        .reduce((prev, curr) => prev && curr) ? (
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
