import IconButton from "@material-ui/core/IconButton";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { PageListProps } from "../../../types";
import PageList from "../../components/PageList";

interface PageListPageProps extends PageListProps {
  pages?: Array<{
    id: string;
    title: string;
    slug: string;
    isVisible: boolean;
  }>;
}

const PageListPage: React.StatelessComponent<PageListPageProps> = ({
  disabled,
  pages,
  pageInfo,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => (
  <Container width="md">
    <PageHeader
      title={i18n.t("Pages", {
        context: "title"
      })}
    >
      <IconButton disabled={disabled} onClick={onAdd}>
        <AddIcon />
      </IconButton>
    </PageHeader>
    <PageList
      disabled={disabled}
      pageInfo={pageInfo}
      pages={pages}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      onRowClick={onRowClick}
    />
  </Container>
);
PageListPage.displayName = "PageListPage";
export default PageListPage;
