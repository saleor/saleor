import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route } from "react-router-dom";

import ActionDialog from "../../components/ActionDialog";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { createPaginationState, Paginator } from "../../components/Paginator";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { productUrl } from "../../products/urls";
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
import { UnassignCollectionProduct } from "../types/UnassignCollectionProduct";
import {
  collectionAddProductPath,
  collectionAddProductUrl,
  collectionImageRemovePath,
  collectionImageRemoveUrl,
  collectionListUrl,
  collectionRemovePath,
  collectionRemoveUrl,
  collectionUrl
} from "../urls";

export type CollectionDetailsQueryParams = Partial<{
  after: string;
  before: string;
}>;

interface CollectionDetailsProps {
  id: string;
  params: CollectionDetailsQueryParams;
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
            <TypedCollectionDetailsQuery
              displayLoader
              variables={{ id, ...paginationState }}
              require={["collection"]}
            >
              {({ data, loading }) => {
                const handleCollectionUpdate = (data: CollectionUpdate) => {
                  if (data.collectionUpdate.errors.length === 0) {
                    pushMessage({
                      text: i18n.t("Updated collection", {
                        context: "notification"
                      })
                    });
                    navigate(collectionUrl(id));
                  }
                };

                const handleProductAssign = (data: CollectionAssignProduct) => {
                  if (data.collectionAddProducts.errors.length === 0) {
                    pushMessage({
                      text: i18n.t("Added product to collection", {
                        context: "notification"
                      })
                    });
                    navigate(collectionUrl(id), true);
                  }
                };

                const handleProductUnassign = (
                  data: UnassignCollectionProduct
                ) => {
                  if (data.collectionRemoveProducts.errors.length === 0) {
                    pushMessage({
                      text: i18n.t("Removed product from collection", {
                        context: "notification"
                      })
                    });
                  }
                };

                const handleCollectionRemove = (data: RemoveCollection) => {
                  if (data.collectionDelete.errors.length === 0) {
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
                    onUpdate={handleCollectionUpdate}
                    onProductAssign={handleProductAssign}
                    onProductUnassign={handleProductUnassign}
                    onRemove={handleCollectionRemove}
                  >
                    {({
                      updateCollection,
                      updateCollectionWithHomepage,
                      assignProduct,
                      unassignProduct,
                      removeCollection
                    }) => {
                      const handleSubmit = (
                        formData: CollectionDetailsPageFormData
                      ) => {
                        const input = {
                          backgroundImageAlt: formData.backgroundImageAlt,
                          description: formData.description,
                          isPublished: formData.isPublished,
                          name: formData.name,
                          seo: {
                            description: formData.seoDescription,
                            title: formData.seoTitle
                          }
                        };
                        const isFeatured = data.shop.homepageCollection
                          ? data.shop.homepageCollection.id ===
                            data.collection.id
                          : false;

                        if (formData.isFeatured !== isFeatured) {
                          updateCollectionWithHomepage.mutate({
                            homepageId: formData.isFeatured ? id : null,
                            id,
                            input
                          });
                        } else {
                          updateCollection.mutate({
                            id,
                            input
                          });
                        }
                      };

                      const formTransitionState = getMutationState(
                        updateCollection.opts.called ||
                          updateCollectionWithHomepage.opts.called,
                        updateCollection.opts.loading ||
                          updateCollectionWithHomepage.opts.loading,
                        maybe(
                          () =>
                            updateCollection.opts.data.collectionUpdate.errors
                        ),
                        maybe(
                          () =>
                            updateCollectionWithHomepage.opts.data
                              .collectionUpdate.errors
                        ),
                        maybe(
                          () =>
                            updateCollectionWithHomepage.opts.data
                              .homepageCollectionUpdate.errors
                        )
                      );
                      const assignTransitionState = getMutationState(
                        assignProduct.opts.called,
                        assignProduct.opts.loading,
                        maybe(
                          () =>
                            assignProduct.opts.data.collectionAddProducts.errors
                        )
                      );
                      const removeTransitionState = getMutationState(
                        removeCollection.opts.called,
                        removeCollection.opts.loading,
                        maybe(
                          () =>
                            removeCollection.opts.data.collectionDelete.errors
                        )
                      );
                      const imageRemoveTransitionState = getMutationState(
                        updateCollection.opts.called,
                        updateCollection.opts.loading,
                        maybe(
                          () =>
                            updateCollection.opts.data.collectionUpdate.errors
                        )
                      );

                      return (
                        <>
                          <WindowTitle
                            title={maybe(() => data.collection.name)}
                          />
                          <Paginator
                            pageInfo={maybe(
                              () => data.collection.products.pageInfo
                            )}
                            paginationState={paginationState}
                            queryString={params}
                          >
                            {({ loadNextPage, loadPreviousPage, pageInfo }) => (
                              <CollectionDetailsPage
                                onAdd={() =>
                                  navigate(
                                    collectionAddProductUrl(id),
                                    false,
                                    true
                                  )
                                }
                                onBack={() => navigate(collectionListUrl)}
                                disabled={loading}
                                collection={data.collection}
                                isFeatured={maybe(
                                  () =>
                                    data.shop.homepageCollection.id ===
                                    data.collection.id,
                                  false
                                )}
                                onCollectionRemove={() =>
                                  navigate(collectionRemoveUrl(id), false, true)
                                }
                                onImageDelete={() =>
                                  navigate(
                                    collectionImageRemoveUrl(id),
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
                                onProductUnassign={(productId, event) => {
                                  event.stopPropagation();
                                  unassignProduct.mutate({
                                    collectionId: id,
                                    productId,
                                    ...paginationState
                                  });
                                }}
                                onRowClick={id => () =>
                                  navigate(productUrl(id))}
                                saveButtonBarState={formTransitionState}
                              />
                            )}
                          </Paginator>
                          <Route
                            path={collectionAddProductPath(":id")}
                            render={({ match }) => (
                              <SearchProductsProvider>
                                {(searchProducts, searchProductsOpts) => (
                                  <CollectionAssignProductDialog
                                    confirmButtonState={assignTransitionState}
                                    open={!!match}
                                    onFetch={searchProducts}
                                    loading={searchProductsOpts.loading}
                                    onClose={() =>
                                      navigate(collectionUrl(id), true, true)
                                    }
                                    onSubmit={formData =>
                                      assignProduct.mutate({
                                        ...paginationState,
                                        collectionId: id,
                                        productIds: formData.products.map(
                                          product => product.id
                                        )
                                      })
                                    }
                                    products={maybe(() =>
                                      searchProductsOpts.data.products.edges
                                        .map(edge => edge.node)
                                        .filter(
                                          suggestedProduct =>
                                            suggestedProduct.id
                                        )
                                    )}
                                  />
                                )}
                              </SearchProductsProvider>
                            )}
                          />
                          <Route
                            path={collectionRemovePath(":id")}
                            render={({ match }) => (
                              <ActionDialog
                                confirmButtonState={removeTransitionState}
                                onClose={() =>
                                  navigate(collectionUrl(id), true, true)
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
                                        collectionName: maybe(
                                          () => data.collection.name
                                        ),
                                        context: "modal"
                                      }
                                    )
                                  }}
                                />
                              </ActionDialog>
                            )}
                          />
                          <Route
                            path={collectionImageRemovePath(":id")}
                            render={({ match }) => (
                              <ActionDialog
                                confirmButtonState={imageRemoveTransitionState}
                                onClose={() =>
                                  navigate(collectionUrl(id), true, true)
                                }
                                onConfirm={() =>
                                  updateCollection.mutate({
                                    id,
                                    input: {
                                      backgroundImage: null
                                    }
                                  })
                                }
                                open={!!match}
                                title={i18n.t("Remove collection", {
                                  context: "modal title"
                                })}
                                variant="delete"
                              >
                                <DialogContentText>
                                  {i18n.t(
                                    "Are you sure you want to remove collection's image?"
                                  )}
                                </DialogContentText>
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
          );
        }}
      </Navigator>
    )}
  </Messages>
);
export default CollectionDetails;
