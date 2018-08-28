import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { Menu } from "../..";
import { PageListProps } from "../../..";
import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import MenuList from "../MenuList/MenuList";

interface MenuListPageProps extends PageListProps {
  menus?: Array<
    Menu & {
      items: {
        totalCount: number;
      };
    }
  >;
}

const MenuListPage: React.StatelessComponent<MenuListPageProps> = ({
  disabled,
  menus,
  onNextPage,
  onPreviousPage,
  onRowClick,
  pageInfo,
  onAdd
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Navigation")}>
      <Button color="secondary" variant="contained" onClick={onAdd}>
        {i18n.t("Add menu")} <AddIcon />
      </Button>
    </PageHeader>
    <MenuList
      disabled={disabled}
      menus={menus}
      pageInfo={pageInfo}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      onRowClick={onRowClick}
    />
  </Container>
);
MenuListPage.displayName = "MenuListPage";
export default MenuListPage;
