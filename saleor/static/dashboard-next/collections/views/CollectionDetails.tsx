import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route } from "react-router-dom";

import ActionDialog from "../../components/ActionDialog";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import i18n from "../../i18n";
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
import { CollectionUpdate } from "../types/CollectionUpdate";
import { RemoveCollection } from "../types/RemoveCollection";
import {
  collectionAddProductUrl,
  collectionImageRemoveUrl,
  collectionListUrl,
  collectionRemoveUrl,
  collectionUrl
} from "../urls";

interface CollectionDetailsProps {
  id: string;
  params: {
    after?: string;
    before?: string;
  };
}

const PAGINATE_BY = 20;

export const CollectionDetails: React.StatelessComponent<
  CollectionDetailsProps
> = ({ id, params }) => (
  <Messages>
    {pushMessage => (
      <Navigator>
        {navigate => {
          const paginationState = createPaginationState(PAGINATE_BY, params);
          return (
            <SearchProductsProvider>
              {(searchProducts, searchProductsOpts) => (
                <TypedCollectionDetailsQuery
                  variables={{ id, ...paginationState }}
                >
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

                    const handleCollectionUpdate = (data: CollectionUpdate) => {
                      if (
                        data.collectionUpdate.errors === null ||
                        data.collectionUpdate.errors.length === 0
                      ) {
                        pushMessage({
                          text: i18n.t("Updated collection", {
                            context: "notification"
                          })
                        });
                      }
                    };

                    const handleProductAssign = (
                      data: CollectionAssignProduct
                    ) => {
                      if (
                        data.collectionAddProducts.errors === null ||
                        data.collectionAddProducts.errors.length === 0
                      ) {
                        pushMessage({
                          text: i18n.t("Added product to collection", {
                            context: "notification"
                          })
                        });
                        navigate(collectionUrl(id), true);
                      }
                    };

                    const handleCollectionRemove = (data: RemoveCollection) => {
                      if (
                        data.collectionDelete.errors === null ||
                        data.collectionDelete.errors.length === 0
                      ) {
                        pushMessage({
                          text: i18n.t("Removed collection", {
                            context: "notification"
                          })
                        });
                        navigate(collectionListUrl);
                      }
                    };
                    return (
                      <CollectionOperations
                        onHomepageCollectionAssign={() => undefined}
                        onUpdate={handleCollectionUpdate}
                        onProductAssign={handleProductAssign}
                        onRemove={handleCollectionRemove}
                      >
                        {({
                          updateCollection,
                          assignHomepageCollection,
                          assignProduct,
                          removeCollection
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
                                    collectionAddProductUrl(
                                      encodeURIComponent(id)
                                    ),
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
                                    collectionRemoveUrl(encodeURIComponent(id)),
                                    false,
                                    true
                                  )
                                }
                                onImageDelete={() =>
                                  navigate(
                                    collectionImageRemoveUrl(
                                      encodeURIComponent(id)
                                    ),
                                    false,
                                    true
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
                              <Route
                                path={collectionRemoveUrl(
                                  encodeURIComponent(id)
                                )}
                                render={({ match }) => (
                                  <ActionDialog
                                    onClose={() =>
                                      navigate(
                                        collectionUrl(encodeURIComponent(id)),
                                        true,
                                        true
                                      )
                                    }
                                    onConfirm={() =>
                                      removeCollection.mutate({ id })
                                    }
                                    open={!!match}
                                    title={i18n.t("Remove collection", {
                                      context: "modal title"
                                    })}
                                    variant="delete"
                                  >
                                    <DialogContentText
                                      dangerouslySetInnerHTML={{
                                        __html: i18n.t(
                                          "Are you sure you want to remove <strong>{{ collectionName }}</strong>?",
                                          {
                                            collectionName:
                                              data.collection.name,
                                            context: "modal"
                                          }
                                        )
                                      }}
                                    />
                                  </ActionDialog>
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
    )}
  </Messages>
);
export default CollectionDetails;
