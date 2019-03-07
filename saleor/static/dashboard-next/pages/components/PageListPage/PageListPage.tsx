import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { PageListProps } from "../../../types";
import { PageList_pages_edges_node } from "../../types/PageList";
import PageList from "../PageList/PageList";

export interface PageListPageProps extends PageListProps {
  pages: PageList_pages_edges_node[];
}

const PageListPage: React.StatelessComponent<PageListPageProps> = ({
  disabled,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick,
  pageInfo,
  pages
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Pages")}>
      <Button
        disabled={disabled}
        onClick={onAdd}
        variant="contained"
        color="secondary"
      >
        {i18n.t("Add page")}
        <AddIcon />
      </Button>
    </PageHeader>
    <PageList
      disabled={disabled}
      pages={pages}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      onRowClick={onRowClick}
      pageInfo={pageInfo}
    />
  </Container>
);
PageListPage.displayName = "PageListPage";
export default PageListPage;
