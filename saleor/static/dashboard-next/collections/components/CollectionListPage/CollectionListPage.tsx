import * as React from "react";

import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import CollectionList from "../CollectionList/CollectionList";

interface CollectionListPageProps {
  collections?: Array<{
    id: string;
    name: string;
    slug: string;
    isPublished: boolean;
    products: {
      totalCount: number;
    };
  }>;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  onCollectionAdd?();
  onCollectionClick?(id: string): () => void;
  onCollectionShow?(slug: string): () => void;
  onNextPage?();
  onPreviousPage?();
}

const CollectionListPage: React.StatelessComponent<CollectionListPageProps> = ({
  collections,
  pageInfo,
  onCollectionAdd,
  onCollectionClick,
  onCollectionShow,
  onNextPage,
  onPreviousPage
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Collections")} />
    <CollectionList
      collections={collections}
      pageInfo={pageInfo}
      onCollectionAdd={onCollectionAdd}
      onCollectionClick={onCollectionClick}
      onCollectionShow={onCollectionShow}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
    />
  </Container>
);
CollectionListPage.displayName = "CollectionListPage";
export default CollectionListPage;
