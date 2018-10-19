import * as React from "react";
import { Route } from "react-router-dom";

import Navigator from "../../components/Navigator";
import { createPaginationData, createPaginationState, maybe } from "../../misc";
import { productUrl } from "../../products";
import CollectionAssignProductDialog from "../components/CollectionAssignProductDialog/CollectionAssignProductDialog";
import CollectionDetailsPage, {
  CollectionDetailsPageFormData
} from "../components/CollectionDetailsPage/CollectionDetailsPage";
import CollectionOperations from "../containers/CollectionOperations";
import { SearchProductsProvider } from "../containers/ProductSearch";
import { TypedCollectionDetailsQuery } from "../queries";
import { CollectionAssignProduct } from "../types/CollectionAssignProduct";
import {
  collectionAddProductUrl,
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
        <SearchProductsProvider>
          {(searchProducts, searchProductsOpts) => (
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

                const handleProductAssign = (data: CollectionAssignProduct) => {
                  if (
                    data.collectionAddProducts.errors === null ||
                    data.collectionAddProducts.errors.length === 0
                  ) {
                    navigate(collectionUrl(id), true);
                  }
                };
                return (
                  <CollectionOperations
                    onHomepageCollectionAssign={() => undefined}
                    onUpdate={() => undefined}
                    onProductAssign={handleProductAssign}
                  >
                    {({
                      updateCollection,
                      assignHomepageCollection,
                      assignProduct
                    }) => {
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
                          (data.shop.homepageCollection.id ===
                            data.collection.id)
                        ) {
                          assignHomepageCollection.mutate({
                            id: formData.isFeatured ? id : null
                          });
                        }
                      };
                      return (
                        <>
                          <CollectionDetailsPage
                            onAdd={() =>
                              navigate(
                                collectionAddProductUrl(encodeURIComponent(id)),
                                false,
                                true
                              )
                            }
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
                              navigate(
                                collectionRemoveUrl(encodeURIComponent(id))
                              )
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
                          <Route
                            path={collectionAddProductUrl(
                              encodeURIComponent(id)
                            )}
                            render={({ match }) => (
                              <CollectionAssignProductDialog
                                open={!!match}
                                fetch={searchProducts}
                                loading={searchProductsOpts.loading}
                                onClose={() =>
                                  navigate(
                                    collectionUrl(encodeURIComponent(id)),
                                    true,
                                    true
                                  )
                                }
                                onSubmit={product =>
                                  assignProduct.mutate({
                                    collectionId: id,
                                    productId: product.product.value
                                  })
                                }
                                products={maybe(() =>
                                  searchProductsOpts.data.products.edges.map(
                                    edge => edge.node
                                  )
                                )}
                              />
                            )}
                          />
                        </>
                      );
                    }}
                  </CollectionOperations>
                );
              }}
            </TypedCollectionDetailsQuery>
          )}
        </SearchProductsProvider>
      );
    }}
  </Navigator>
);
export default CollectionDetails;
