import { withStyles } from "@material-ui/core/styles";
import * as React from "react";
import { ListProps } from "../../..";

interface MenuListPageProps extends ListProps {
  menus?: Menu[];
}

const decorate = withStyles(theme => ({ root: {} }));
const MenuListPage = decorate<MenuListPageProps>(({ classes }) => <div />);
MenuListPage.displayName = "MenuListPage";
export default MenuListPage;
