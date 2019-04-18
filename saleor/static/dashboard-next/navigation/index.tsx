import { parse as parseQs } from "qs";
import * as React from "react";
import { Route, RouteComponentProps, Switch } from "react-router-dom";

import { menuListPath } from "./urls";
import MenuListComponent from "./views/MenuList";

const MenuList: React.FC<RouteComponentProps<{}>> = ({ location }) => {
  const qs = parseQs(location.search.substr(1));
  return <MenuListComponent params={qs} />;
};

const NavigationRouter: React.FC = () => (
  <Switch>
    <Route exact component={MenuList} path={menuListPath} />
  </Switch>
);

export default NavigationRouter;
