import * as React from "react";

import Container from "../../../components/Container";
import { ListActions, PageListProps } from "../../../types";
import { MenuList_menus_edges_node } from "../../types/MenuList";
import MenuList from "../MenuList/MenuList";

export interface MenuListPageProps extends PageListProps, ListActions {
  menus: MenuList_menus_edges_node[];
  onDelete: (id: string) => void;
}

const MenuListPage: React.StatelessComponent<MenuListPageProps> = ({
  disabled,
  ...listProps
}) => (
  <Container>
    <MenuList disabled={disabled} {...listProps} />
  </Container>
);
MenuListPage.displayName = "MenuListPage";
export default MenuListPage;
