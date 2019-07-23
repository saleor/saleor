import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import Container from "@saleor/components/Container";
import PageHeader from "@saleor/components/PageHeader";
import i18n from "@saleor/i18n";
import { ListActions, PageListProps } from "@saleor/types";
import { PageList_pages_edges_node } from "../../types/PageList";
import PageList from "../PageList/PageList";

export interface PageListPageProps extends PageListProps, ListActions {
  pages: PageList_pages_edges_node[];
  onBack: () => void;
}

const PageListPage: React.StatelessComponent<PageListPageProps> = ({
  disabled,
  settings,
  onAdd,
  onBack,
  onNextPage,
  onPreviousPage,
  onRowClick,
  onUpdateListSettings,
  pageInfo,
  pages,
  isChecked,
  selected,
  toggle,
  toggleAll,
  toolbar
}) => (
  <Container>
    <AppHeader onBack={onBack}>{i18n.t("Configuration")}</AppHeader>
    <PageHeader title={i18n.t("Pages")}>
      <Button
        disabled={disabled}
        onClick={onAdd}
        variant="contained"
        color="primary"
      >
        {i18n.t("Add page")}
        <AddIcon />
      </Button>
    </PageHeader>
    <PageList
      disabled={disabled}
      settings={settings}
      pages={pages}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      onUpdateListSettings={onUpdateListSettings}
      onRowClick={onRowClick}
      pageInfo={pageInfo}
      isChecked={isChecked}
      selected={selected}
      toggle={toggle}
      toggleAll={toggleAll}
      toolbar={toolbar}
    />
  </Container>
);
PageListPage.displayName = "PageListPage";
export default PageListPage;
