import Button from "@material-ui/core/Button";
import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import AssignProductDialog from "../../components/AssignProductDialog";
import { createPaginationState } from "../../components/Paginator";
import { WindowTitle } from "../../components/WindowTitle";
import { SearchProductsProvider } from "../../containers/SearchProducts";
import useBulkActions from "../../hooks/useBulkActions";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import { productUrl } from "../../products/urls";
import { CollectionInput } from "../../types/globalTypes";
import CollectionDetailsPage, {
  CollectionDetailsPageFormData
} from "../components/CollectionDetailsPage/CollectionDetailsPage";
import CollectionOperations from "../containers/CollectionOperations";
import { TypedCollectionDetailsQuery } from "../queries";
import { CollectionAssignProduct } from "../types/CollectionAssignProduct";
import { CollectionUpdate } from "../types/CollectionUpdate";
import { RemoveCollection } from "../types/RemoveCollection";
import { UnassignCollectionProduct } from "../types/UnassignCollectionProduct";
import {
  collectionListUrl,
  collectionUrl,
  CollectionUrlDialog,
  CollectionUrlQueryParams
} from "../urls";

interface CollectionDetailsProps {
  id: string;
  params: CollectionUrlQueryParams;
}

const PAGINATE_BY = 20;

export const CollectionDetails: React.StatelessComponent<
  CollectionDetailsProps
> = ({ id, params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const { isSelected, listElements, reset, toggle } = useBulkActions(
    params.ids
  );
  const paginate = usePaginator();

  const closeModal = () =>
    navigate(
      collectionUrl(id, {
        ...params,
        action: undefined
      }),
      true
    );
  const openModal = (action: CollectionUrlDialog) =>
    navigate(
      collectionUrl(id, {
        ...params,
        action
      }),
      false
    );

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
            notify({
              text: i18n.t("Updated collection", {
                context: "notification"
              })
            });
            navigate(collectionUrl(id));
          } else {
            const backgroundImageError = data.collectionUpdate.errors.find(
              error =>
                error.field === ("backgroundImage" as keyof CollectionInput)
            );
            if (backgroundImageError) {
              notify({
                text: backgroundImageError.message
              });
            }
          }
        };

        const handleProductAssign = (data: CollectionAssignProduct) => {
          if (data.collectionAddProducts.errors.length === 0) {
            notify({
              text: i18n.t("Added product to collection", {
                context: "notification"
              })
            });
            navigate(collectionUrl(id), true);
          }
        };

        const handleProductUnassign = (data: UnassignCollectionProduct) => {
          if (data.collectionRemoveProducts.errors.length === 0) {
            notify({
              text: i18n.t("Removed product from collection", {
                context: "notification"
              })
            });
            reset();
            closeModal();
          }
        };

        const handleCollectionRemove = (data: RemoveCollection) => {
          if (data.collectionDelete.errors.length === 0) {
            notify({
              text: i18n.t("Removed collection", {
                context: "notification"
              })
            });
            navigate(collectionListUrl());
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
                  descriptionJson: JSON.stringify(formData.description),
                  isPublished: formData.isPublished,
                  name: formData.name,
                  seo: {
                    description: formData.seoDescription,
                    title: formData.seoTitle
                  }
                };
                const isFeatured = data.shop.homepageCollection
                  ? data.shop.homepageCollection.id === data.collection.id
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
                maybe(() => updateCollection.opts.data.collectionUpdate.errors),
                maybe(
                  () =>
                    updateCollectionWithHomepage.opts.data.collectionUpdate
                      .errors
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
                  () => assignProduct.opts.data.collectionAddProducts.errors
                )
              );
              const unassignTransitionState = getMutationState(
                unassignProduct.opts.called,
                unassignProduct.opts.loading,
                maybe(
                  () =>
                    unassignProduct.opts.data.collectionRemoveProducts.errors
                )
              );
              const removeTransitionState = getMutationState(
                removeCollection.opts.called,
                removeCollection.opts.loading,
                maybe(() => removeCollection.opts.data.collectionDelete.errors)
              );
              const imageRemoveTransitionState = getMutationState(
                updateCollection.opts.called,
                updateCollection.opts.loading,
                maybe(() => updateCollection.opts.data.collectionUpdate.errors)
              );

              const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
                maybe(() => data.collection.products.pageInfo),
                paginationState,
                params
              );

              return (
                <>
                  <WindowTitle title={maybe(() => data.collection.name)} />
                  <CollectionDetailsPage
                    onAdd={() => openModal("assign")}
                    onBack={() => navigate(collectionListUrl())}
                    disabled={loading}
                    collection={data.collection}
                    isFeatured={maybe(
                      () =>
                        data.shop.homepageCollection.id === data.collection.id,
                      false
                    )}
                    onCollectionRemove={() => openModal("remove")}
                    onImageDelete={() => openModal("removeImage")}
                    onImageUpload={file =>
                      updateCollection.mutate({
                        id,
                        input: {
                          backgroundImage: file
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
                        productIds: [productId],
                        ...paginationState
                      });
                    }}
                    onRowClick={id => () => navigate(productUrl(id))}
                    saveButtonBarState={formTransitionState}
                    toolbar={
                      <Button
                        color="primary"
                        onClick={() =>
                          navigate(
                            collectionUrl(id, {
                              action: "unassign",
                              ids: listElements
                            })
                          )
                        }
                      >
                        {i18n.t("Unassign")}
                      </Button>
                    }
                    isChecked={isSelected}
                    selected={listElements.length}
                    toggle={toggle}
                  />
                  <SearchProductsProvider>
                    {(searchProducts, searchProductsOpts) => (
                      <AssignProductDialog
                        confirmButtonState={assignTransitionState}
                        open={params.action === "assign"}
                        onFetch={searchProducts}
                        loading={searchProductsOpts.loading}
                        onClose={() => navigate(collectionUrl(id), true, true)}
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
                            .filter(suggestedProduct => suggestedProduct.id)
                        )}
                      />
                    )}
                  </SearchProductsProvider>
                  <ActionDialog
                    confirmButtonState={removeTransitionState}
                    onClose={closeModal}
                    onConfirm={() => removeCollection.mutate({ id })}
                    open={params.action === "remove"}
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
                              () => data.collection.name,
                              "..."
                            ),
                            context: "modal"
                          }
                        )
                      }}
                    />
                  </ActionDialog>
                  <ActionDialog
                    confirmButtonState={unassignTransitionState}
                    onClose={closeModal}
                    onConfirm={() =>
                      unassignProduct.mutate({
                        ...paginationState,
                        collectionId: id,
                        productIds: params.ids
                      })
                    }
                    open={params.action === "unassign"}
                    title={i18n.t("Unassign products from collection", {
                      context: "modal title"
                    })}
                  >
                    <DialogContentText
                      dangerouslySetInnerHTML={{
                        __html: i18n.t(
                          "Are you sure you want to unassign <strong>{{ number }}</strong> products?",
                          {
                            context: "modal",
                            number: maybe(
                              () => params.ids.length.toString(),
                              "..."
                            )
                          }
                        )
                      }}
                    />
                  </ActionDialog>
                  <ActionDialog
                    confirmButtonState={imageRemoveTransitionState}
                    onClose={closeModal}
                    onConfirm={() =>
                      updateCollection.mutate({
                        id,
                        input: {
                          backgroundImage: null
                        }
                      })
                    }
                    open={params.action === "removeImage"}
                    title={i18n.t("Remove image", {
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
                </>
              );
            }}
          </CollectionOperations>
        );
      }}
    </TypedCollectionDetailsQuery>
  );
};
export default CollectionDetails;
