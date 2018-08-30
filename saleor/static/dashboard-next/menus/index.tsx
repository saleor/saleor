import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import MenuListComponent from "./views/MenuList";

const MenuList: React.StatelessComponent<RouteComponentProps<{}>> = ({
  location
}) => {
  const qs = parseQs(location.search.substr(1));
  const params = {
    after: qs.after,
    before: qs.before
  };
  return <MenuListComponent params={params} />;
};

export const MenuRouter: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => (
  <Switch>
    <Route exact path={match.url} component={MenuList} />
  </Switch>
);

export interface Menu {
  id: string;
  name: string;
}

export interface MenuItem {
  id: string;
  name: string;
  url: string;
}

export const menuListUrl = "/menus/";
export const menuAddUrl = "/menus/add/";
export const menuUrl = (id: string) => `/menus/${id}/`;

export default MenuRouter;
