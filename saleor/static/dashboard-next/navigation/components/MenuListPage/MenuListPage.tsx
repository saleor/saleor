import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { ListActions, PageListProps } from "../../../types";
import { MenuList_menus_edges_node } from "../../types/MenuList";
import MenuList from "../MenuList";

export interface MenuListPageProps extends PageListProps, ListActions {
  menus: MenuList_menus_edges_node[];
  onBack: () => void;
  onDelete: (id: string) => void;
}

const MenuListPage: React.StatelessComponent<MenuListPageProps> = ({
  disabled,
  onAdd,
  onBack,
  ...listProps
}) => (
  <Container>
    <AppHeader onBack={onBack}>{i18n.t("Configuration")}</AppHeader>
    <PageHeader title={i18n.t("Navigation")}>
      <Button
        color="primary"
        disabled={disabled}
        variant="contained"
        onClick={onAdd}
      >
        {i18n.t("Add Menu")} <AddIcon />
      </Button>
    </PageHeader>
    <MenuList disabled={disabled} {...listProps} />
  </Container>
);
MenuListPage.displayName = "MenuListPage";
export default MenuListPage;
