import AddIcon from "@material-ui/icons/Add";
import Card from "material-ui/Card";
import IconButton from "material-ui/IconButton";
import { withStyles } from "material-ui/styles";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import PageList from "../../components/PageList";

interface PageListPageProps {
  pages?: Array<{
    id: string;
    title: string;
    slug: string;
    isVisible: boolean;
  }>;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  onAddPage?();
  onBack?();
  onEditPage?(id: string);
  onNextPage?();
  onPreviousPage?();
  onShowPage?(slug: string);
}

const decorate = withStyles(theme => ({ root: {} }));
const PageListPage = decorate<PageListPageProps>(
  ({
    classes,
    pages,
    pageInfo,
    onAddPage,
    onBack,
    onEditPage,
    onNextPage,
    onPreviousPage,
    onShowPage
  }) => (
    <Container width="md">
      <PageHeader
        title={i18n.t("Pages", {
          context: "title"
        })}
      >
        <IconButton disabled={!onAddPage} onClick={onAddPage}>
          <AddIcon />
        </IconButton>
      </PageHeader>
      <PageList
        pageInfo={pageInfo}
        pages={pages}
        onNextPage={onNextPage}
        onPreviousPage={onPreviousPage}
        onEditClick={onEditPage}
        onShowPageClick={onShowPage}
      />
    </Container>
  )
);
export default PageListPage;
