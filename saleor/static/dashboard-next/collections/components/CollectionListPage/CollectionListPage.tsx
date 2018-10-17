import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { PageListProps } from "../../..";
import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { CollectionList_collections_edges_node } from "../../types/CollectionList";

interface CollectionListPageProps extends PageListProps {
  collections: CollectionList_collections_edges_node[];
}

const CollectionListPage: React.StatelessComponent<CollectionListPageProps> = ({
  disabled,
  onAdd,
  ...listProps
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Collections", { context: "page title" })}>
      <Button
        color="secondary"
        disabled={disabled}
        variant="contained"
        onClick={onAdd}
      >
        {i18n.t("Add collections", { context: "button" })}
        <AddIcon />
      </Button>
    </PageHeader>
  </Container>
);
CollectionListPage.displayName = "CollectionListPage";
export default CollectionListPage;
