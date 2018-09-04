import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { PageListProps } from "../../..";
import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import CollectionList from "../CollectionList/CollectionList";

interface CollectionListPageProps extends PageListProps {
  collections?: Array<{
    id: string;
    name: string;
    slug: string;
    isPublished: boolean;
    products: {
      totalCount: number;
    };
  }>;
}

const CollectionListPage: React.StatelessComponent<CollectionListPageProps> = ({
  collections,
  disabled,
  pageInfo,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Collections")}>
      <Button
        color="secondary"
        variant="contained"
        disabled={disabled}
        onClick={onAdd}
      >
        {i18n.t("Add collection")} <AddIcon />
      </Button>
    </PageHeader>
    <CollectionList
      collections={collections}
      disabled={disabled}
      pageInfo={pageInfo}
      onRowClick={onRowClick}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
    />
  </Container>
);
CollectionListPage.displayName = "CollectionListPage";
export default CollectionListPage;
