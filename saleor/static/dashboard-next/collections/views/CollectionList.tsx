import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationData, createPaginationState, maybe } from "../../misc";
import CollectionListPage from "../components/CollectionListPage/CollectionListPage";
import { TypedCollectionListQuery } from "../queries";
import { collectionAddUrl, collectionListUrl, collectionUrl } from "../urls";

interface CollectionListProps {
  params: {
    after?: string;
    before?: string;
  };
}

const PAGINATE_BY = 20;

export const CollectionList: React.StatelessComponent<CollectionListProps> = ({
  params
}) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedCollectionListQuery variables={paginationState}>
          {({ data, loading }) => {
            const {
              loadNextPage,
              loadPreviousPage,
              pageInfo
            } = createPaginationData(
              navigate,
              paginationState,
              collectionListUrl,
              maybe(() => data.collections.pageInfo),
              loading
            );
            return (
              <CollectionListPage
                onAdd={() => navigate(collectionAddUrl)}
                disabled={loading}
                collections={maybe(() =>
                  data.collections.edges.map(edge => edge.node)
                )}
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
                pageInfo={pageInfo}
                onRowClick={id => () =>
                  navigate(collectionUrl(encodeURIComponent(id)))}
              />
            );
          }}
        </TypedCollectionListQuery>
      );
    }}
  </Navigator>
);
export default CollectionList;
