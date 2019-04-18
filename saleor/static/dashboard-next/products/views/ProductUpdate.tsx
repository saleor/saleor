import DialogContentText from "@material-ui/core/DialogContentText";
import IconButton from "@material-ui/core/IconButton";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";
import { arrayMove } from "react-sortable-hoc";

import * as placeholderImg from "../../../images/placeholder255x255.png";
import ActionDialog from "../../components/ActionDialog";
import { WindowTitle } from "../../components/WindowTitle";
import useBulkActions from "../../hooks/useBulkActions";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import i18n from "../../i18n";
import { decimal, getMutationState, maybe } from "../../misc";
import { productTypeUrl } from "../../productTypes/urls";
import ProductUpdatePage, { FormData } from "../components/ProductUpdatePage";
import { CategorySearchProvider } from "../containers/CategorySearch";
import { CollectionSearchProvider } from "../containers/CollectionSearch";
import ProductUpdateOperations from "../containers/ProductUpdateOperations";
import { TypedProductDetailsQuery } from "../queries";
import {
  ProductImageCreate,
  ProductImageCreateVariables
} from "../types/ProductImageCreate";
import { ProductVariantBulkDelete } from "../types/ProductVariantBulkDelete";
import {
  productImageUrl,
  productListUrl,
  productUrl,
  ProductUrlQueryParams,
  productVariantAddUrl,
  productVariantEditUrl
} from "../urls";

interface ProductUpdateProps {
  id: string;
  params: ProductUrlQueryParams;
}

export const ProductUpdate: React.StatelessComponent<ProductUpdateProps> = ({
  id,
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const { isSelected, listElements, reset, toggle } = useBulkActions(
    params.ids
  );

  return (
    <CategorySearchProvider>
      {({ search: searchCategories, searchOpts: searchCategoriesOpts }) => (
        <CollectionSearchProvider>
          {({
            search: searchCollections,
            searchOpts: searchCollectionsOpts
          }) => (
            <TypedProductDetailsQuery
              displayLoader
              require={["product"]}
              variables={{ id }}
            >
              {({ data, loading, refetch }) => {
                const handleDelete = () => {
                  notify({ text: i18n.t("Product removed") });
                  navigate(productListUrl());
                };
                const handleUpdate = () =>
                  notify({ text: i18n.t("Saved changes") });
                const handleImageCreate = (data: ProductImageCreate) => {
                  const imageError = data.productImageCreate.errors.find(
                    error =>
                      error.field ===
                      ("image" as keyof ProductImageCreateVariables)
                  );
                  if (imageError) {
                    notify({
                      text: imageError.message
                    });
                  }
                };
                const handleImageDeleteSuccess = () =>
                  notify({
                    text: i18n.t("Image successfully deleted")
                  });
                const handleVariantAdd = () =>
                  navigate(productVariantAddUrl(id));

                const handleBulkProductVariantDelete = (
                  data: ProductVariantBulkDelete
                ) => {
                  if (data.productVariantBulkDelete.errors.length === 0) {
                    navigate(productUrl(id), true);
                    reset();
                    refetch();
                  }
                };

                const product = data ? data.product : undefined;
                return (
                  <ProductUpdateOperations
                    product={product}
                    onBulkProductVariantDelete={handleBulkProductVariantDelete}
                    onDelete={handleDelete}
                    onImageCreate={handleImageCreate}
                    onImageDelete={handleImageDeleteSuccess}
                    onUpdate={handleUpdate}
                  >
                    {({
                      bulkProductVariantDelete,
                      createProductImage,
                      deleteProduct,
                      deleteProductImage,
                      reorderProductImages,
                      updateProduct,
                      updateSimpleProduct
                    }) => {
                      const handleImageDelete = (id: string) => () =>
                        deleteProductImage.mutate({ id });
                      const handleImageEdit = (imageId: string) => () =>
                        navigate(productImageUrl(id, imageId));
                      const handleSubmit = (data: FormData) => {
                        if (product) {
                          if (product.productType.hasVariants) {
                            updateProduct.mutate({
                              attributes: data.attributes,
                              category: data.category.value,
                              chargeTaxes: data.chargeTaxes,
                              collections: data.collections.map(
                                collection => collection.value
                              ),
                              descriptionJson: JSON.stringify(data.description),
                              id: product.id,
                              isPublished: data.available,
                              name: data.name,
                              price: decimal(data.price),
                              publicationDate:
                                data.publicationDate !== ""
                                  ? data.publicationDate
                                  : null
                            });
                          } else {
                            updateSimpleProduct.mutate({
                              attributes: data.attributes,
                              category: data.category.value,
                              chargeTaxes: data.chargeTaxes,
                              collections: data.collections.map(
                                collection => collection.value
                              ),
                              descriptionJson: JSON.stringify(data.description),
                              id: product.id,
                              isPublished: data.available,
                              name: data.name,
                              price: decimal(data.price),
                              productVariantId: product.variants[0].id,
                              productVariantInput: {
                                quantity: data.stockQuantity,
                                sku: data.sku
                              },
                              publicationDate:
                                data.publicationDate !== ""
                                  ? data.publicationDate
                                  : null
                            });
                          }
                        }
                      };

                      const disableFormSave =
                        createProductImage.opts.loading ||
                        deleteProduct.opts.loading ||
                        reorderProductImages.opts.loading ||
                        updateProduct.opts.loading ||
                        loading;
                      const formTransitionState = getMutationState(
                        updateProduct.opts.called ||
                          updateSimpleProduct.opts.called,
                        updateProduct.opts.loading ||
                          updateSimpleProduct.opts.loading,
                        maybe(
                          () => updateProduct.opts.data.productUpdate.errors
                        ),
                        maybe(
                          () =>
                            updateSimpleProduct.opts.data.productUpdate.errors
                        ),
                        maybe(
                          () =>
                            updateSimpleProduct.opts.data.productVariantUpdate
                              .errors
                        )
                      );
                      const deleteTransitionState = getMutationState(
                        deleteProduct.opts.called,
                        deleteProduct.opts.loading,
                        maybe(
                          () => deleteProduct.opts.data.productDelete.errors
                        )
                      );

                      const bulkProductVariantDeleteTransitionState = getMutationState(
                        bulkProductVariantDelete.opts.called,
                        bulkProductVariantDelete.opts.loading,
                        maybe(
                          () =>
                            bulkProductVariantDelete.opts.data
                              .productVariantBulkDelete.errors
                        )
                      );

                      return (
                        <>
                          <WindowTitle title={maybe(() => data.product.name)} />
                          <ProductUpdatePage
                            categories={maybe(
                              () => searchCategoriesOpts.data.categories.edges,
                              []
                            ).map(edge => edge.node)}
                            collections={maybe(
                              () =>
                                searchCollectionsOpts.data.collections.edges,
                              []
                            ).map(edge => edge.node)}
                            disabled={disableFormSave}
                            errors={maybe(
                              () =>
                                updateProduct.opts.data.productUpdate.errors,
                              []
                            )}
                            fetchCategories={searchCategories}
                            fetchCollections={searchCollections}
                            saveButtonBarState={formTransitionState}
                            images={maybe(() => data.product.images)}
                            header={maybe(() => product.name)}
                            placeholderImage={placeholderImg}
                            product={product}
                            productCollections={maybe(
                              () => product.collections
                            )}
                            variants={maybe(() => product.variants)}
                            onAttributesEdit={() =>
                              navigate(
                                productTypeUrl(data.product.productType.id)
                              )
                            }
                            onBack={() => {
                              navigate(productListUrl());
                            }}
                            onDelete={() =>
                              navigate(
                                productUrl(id, {
                                  action: "remove"
                                })
                              )
                            }
                            onProductShow={() => {
                              if (product) {
                                window.open(product.url);
                              }
                            }}
                            onImageReorder={({ newIndex, oldIndex }) => {
                              if (product) {
                                let ids = product.images.map(image => image.id);
                                ids = arrayMove(ids, oldIndex, newIndex);
                                reorderProductImages.mutate({
                                  imagesIds: ids,
                                  productId: product.id
                                });
                              }
                            }}
                            onSubmit={handleSubmit}
                            onVariantAdd={handleVariantAdd}
                            onVariantShow={variantId => () =>
                              navigate(
                                productVariantEditUrl(product.id, variantId)
                              )}
                            onImageUpload={file => {
                              if (product) {
                                createProductImage.mutate({
                                  alt: "",
                                  image: file,
                                  product: product.id
                                });
                              }
                            }}
                            onImageEdit={handleImageEdit}
                            onImageDelete={handleImageDelete}
                            toolbar={
                              <IconButton
                                color="primary"
                                onClick={() =>
                                  navigate(
                                    productUrl(id, {
                                      action: "remove-variants",
                                      ids: listElements
                                    })
                                  )
                                }
                              >
                                <DeleteIcon />
                              </IconButton>
                            }
                            isChecked={isSelected}
                            selected={listElements.length}
                            toggle={toggle}
                          />
                          <ActionDialog
                            open={params.action === "remove"}
                            onClose={() => navigate(productUrl(id), true)}
                            confirmButtonState={deleteTransitionState}
                            onConfirm={() => deleteProduct.mutate({ id })}
                            variant="delete"
                            title={i18n.t("Remove product")}
                          >
                            <DialogContentText
                              dangerouslySetInnerHTML={{
                                __html: i18n.t(
                                  "Are you sure you want to remove <strong>{{ name }}</strong>?",
                                  {
                                    name: product ? product.name : undefined
                                  }
                                )
                              }}
                            />
                          </ActionDialog>
                          <ActionDialog
                            open={params.action === "remove-variants"}
                            onClose={() => navigate(productUrl(id), true)}
                            confirmButtonState={
                              bulkProductVariantDeleteTransitionState
                            }
                            onConfirm={() =>
                              bulkProductVariantDelete.mutate({
                                ids: params.ids
                              })
                            }
                            variant="delete"
                            title={i18n.t("Remove product variants")}
                          >
                            <DialogContentText
                              dangerouslySetInnerHTML={{
                                __html: i18n.t(
                                  "Are you sure you want to remove <strong>{{ number }}</strong> variants?",
                                  {
                                    number: maybe(
                                      () => params.ids.length.toString(),
                                      "..."
                                    )
                                  }
                                )
                              }}
                            />
                          </ActionDialog>
                        </>
                      );
                    }}
                  </ProductUpdateOperations>
                );
              }}
            </TypedProductDetailsQuery>
          )}
        </CollectionSearchProvider>
      )}
    </CategorySearchProvider>
  );
};
export default ProductUpdate;
