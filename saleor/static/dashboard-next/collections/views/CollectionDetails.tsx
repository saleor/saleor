import * as React from "react";

import Navigator from "../../components/Navigator";
import { createPaginationData, createPaginationState, maybe } from "../../misc";
import { productUrl } from "../../products";
import CollectionDetailsPage, {
  CollectionDetailsPageFormData
} from "../components/CollectionDetailsPage/CollectionDetailsPage";
import CollectionOperations from "../containers/CollectionOperations";
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
              <CollectionOperations
                onHomepageCollectionAssign={() => undefined}
                onUpdate={() => undefined}
              >
                {({ updateCollection, assignHomepageCollection }) => {
                  const handleSubmit = (
                    formData: CollectionDetailsPageFormData
                  ) => {
                    updateCollection.mutate({
                      id,
                      input: {
                        isPublished: formData.isPublished,
                        name: formData.name,
                        seo: {
                          description: formData.seoDescription,
                          title: formData.seoTitle
                        }
                      }
                    });
                    if (
                      formData.isFeatured !==
                      (data.shop.homepageCollection.id === data.collection.id)
                    ) {
                      assignHomepageCollection.mutate({
                        id: formData.isFeatured ? id : null
                      });
                    }
                  };
                  return (
                    <CollectionDetailsPage
                      onAdd={() => navigate(collectionAddUrl)}
                      onBack={() => navigate(collectionListUrl)}
                      disabled={loading}
                      collection={maybe(() => data.collection)}
                      isFeatured={maybe(
                        () =>
                          data.shop.homepageCollection.id ===
                          data.collection.id,
                        false
                      )}
                      onCollectionRemove={() =>
                        navigate(collectionRemoveUrl(encodeURIComponent(id)))
                      }
                      onImageDelete={() =>
                        navigate(
                          collectionImageRemoveUrl(encodeURIComponent(id))
                        )
                      }
                      onImageUpload={event =>
                        updateCollection.mutate({
                          id,
                          input: {
                            backgroundImage: event.target.files[0]
                          }
                        })
                      }
                      onSubmit={handleSubmit}
                      onNextPage={loadNextPage}
                      onPreviousPage={loadPreviousPage}
                      pageInfo={pageInfo}
                      onRowClick={id => () =>
                        navigate(productUrl(encodeURIComponent(id)))}
                    />
                  );
                }}
              </CollectionOperations>
            );
          }}
        </TypedCollectionDetailsQuery>
      );
    }}
  </Navigator>
);
export default CollectionDetails;
