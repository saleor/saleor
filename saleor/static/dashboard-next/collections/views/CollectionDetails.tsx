import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationData, createPaginationState, maybe } from "../../misc";
import { productUrl } from "../../products";
import CollectionDetailsPage from "../components/CollectionDetailsPage/CollectionDetailsPage";
import { TypedCollectionDetailsQuery } from "../queries";
import {
  collectionAddUrl,
  collectionImageRemoveUrl,
  collectionListUrl,
  collectionRemoveUrl,
  collectionUrl
} from "../urls";

interface CollectionListProps {
  id: string;
  params: {
    after?: string;
    before?: string;
  };
}

const PAGINATE_BY = 20;

export const CollectionDetails: React.StatelessComponent<
  CollectionListProps
> = ({ id, params }) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedCollectionDetailsQuery variables={{ id, ...paginationState }}>
          {({ data, loading }) => {
            const {
              loadNextPage,
              loadPreviousPage,
              pageInfo
            } = createPaginationData(
              navigate,
              paginationState,
              collectionUrl(encodeURIComponent(id)),
              maybe(() => data.collection.products.pageInfo),
              loading
            );
            return (
              <CollectionDetailsPage
                onAdd={() => navigate(collectionAddUrl)}
                onBack={() => navigate(collectionListUrl)}
                disabled={loading}
                collection={maybe(() => data.collection)}
                isFeatured={maybe(
                  () => data.shop.homepageCollection.id === data.collection.id,
                  false
                )}
                onCollectionRemove={() =>
                  navigate(collectionRemoveUrl(encodeURIComponent(id)))
                }
                onImageDelete={() =>
                  navigate(collectionImageRemoveUrl(encodeURIComponent(id)))
                }
                onImageUpload={() => undefined}
                onSubmit={() => undefined}
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
                pageInfo={pageInfo}
                onRowClick={id => () =>
                  navigate(productUrl(encodeURIComponent(id)))}
              />
            );
          }}
        </TypedCollectionDetailsQuery>
      );
    }}
  </Navigator>
);
export default CollectionDetails;
