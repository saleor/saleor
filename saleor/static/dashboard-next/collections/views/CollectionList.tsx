import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import { maybe } from "../../misc";
import CollectionListPage from "../components/CollectionListPage/CollectionListPage";
import { TypedCollectionListQuery } from "../queries";
import { collectionAddUrl, collectionUrl } from "../urls";

export type CollectionListQueryParams = Partial<{
  after: string;
  before: string;
}>;

interface CollectionListProps {
  params: CollectionListQueryParams;
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
          {({ data, loading }) => (
            <Paginator
              pageInfo={maybe(() => data.collections.pageInfo)}
              paginationState={paginationState}
              queryString={params}
            >
              {({ loadNextPage, loadPreviousPage, pageInfo }) => (
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
              )}
            </Paginator>
          )}
        </TypedCollectionListQuery>
      );
    }}
  </Navigator>
);
export default CollectionList;
