import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import i18n from "../i18n";
import MenuDetailsComponent from "./views/MenuDetails";
import MenuItemDetailsComponent from "./views/MenuItemDetails";
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

const MenuDetails: React.StatelessComponent<
  RouteComponentProps<{ id: string }>
> = ({ location, match }) => {
  const qs = parseQs(location.search.substr(1));
  const params = {
    after: qs.after,
    before: qs.before
  };
  return <MenuDetailsComponent id={match.params.id} params={params} />;
};

const MenuItemDetails: React.StatelessComponent<
  RouteComponentProps<{ id: string }>
> = ({ location, match }) => {
  const qs = parseQs(location.search.substr(1));
  const params = {
    after: qs.after,
    before: qs.before
  };
  return <MenuItemDetailsComponent id={match.params.id} params={params} />;
};

export const MenuRouter: React.StatelessComponent<RouteComponentProps<any>> = ({
  match
}) => (
  <Switch>
    <Route exact path={match.url} component={MenuList} />
    <Route exact path={`${match.url}/item/:id/`} component={MenuItemDetails} />
    <Route exact path={`${match.url}/:id/`} component={MenuDetails} />
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
  category: {
    id: string;
    name: string;
  } | null;
  collection: {
    id: string;
    name: string;
  } | null;
  page: {
    id: string;
    name: string;
  } | null;
}
export interface MenuItemInput {
  name: string;
  type: MenuItemLinkedObjectType;
  value: string;
}

export function menuItemLabelTarget(menuItem: MenuItem) {
  if (menuItem === undefined) {
    return undefined;
  }
  if (menuItem.category) {
    return i18n.t("Category:{{ categoryName }}", {
      categoryName: menuItem.category.name,
      context: "submenu target label"
    });
  }
  if (menuItem.collection) {
    return i18n.t("Collection:{{ collectionName }}", {
      collectionName: menuItem.collection.name,
      context: "submenu target label"
    });
  }
  if (menuItem.page) {
    return i18n.t("Page:{{ pageName }}", {
      context: "submenu target label",
      pageName: menuItem.page.name
    });
  }
  return menuItem.url;
}

export const menuListUrl = "/menus/";
export const menuAddUrl = "/menus/add/";
export const menuUrl = (id: string) => `/menus/${id}/`;
export const menuItemAddUrl = "/menus/item/add/";
export const menuItemUrl = (id: string) => `/menus/item/${id}/`;

export enum MenuItemLinkedObjectType {
  category = "category",
  collection = "collection",
  page = "page",
  staticUrl = "url"
}

export default MenuRouter;
