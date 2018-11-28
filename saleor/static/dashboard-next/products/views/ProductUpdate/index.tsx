import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route } from "react-router-dom";
import { arrayMove } from "react-sortable-hoc";

import * as placeholderImg from "../../../../images/placeholder255x255.png";
import ActionDialog from "../../../components/ActionDialog";
import ErrorMessageCard from "../../../components/ErrorMessageCard";
import Messages from "../../../components/messages";
import Navigator from "../../../components/Navigator";
import { WindowTitle } from "../../../components/WindowTitle";
import i18n from "../../../i18n";
import { decimal, getMutationState, maybe } from "../../../misc";
import { productTypeUrl } from "../../../productTypes/urls";
import ProductUpdatePage from "../../components/ProductUpdatePage";
import ProductUpdateOperations from "../../containers/ProductUpdateOperations";
import { TypedProductDetailsQuery } from "../../queries";
import {
  productImageUrl,
  productListUrl,
  productUrl,
  productVariantAddUrl,
  productVariantEditUrl
} from "../../urls";
import { productRemovePath, productRemoveUrl } from "./urls";

interface ProductUpdateProps {
  id: string;
}

export const ProductUpdate: React.StatelessComponent<ProductUpdateProps> = ({
  id
}) => (
  <Messages>
    {pushMessage => {
      return (
        <Navigator>
          {navigate => {
            return (
              <TypedProductDetailsQuery displayLoader variables={{ id }}>
                {({ data, loading, error }) => {
                  if (error) {
                    return <ErrorMessageCard message="Something went wrong" />;
                  }

                  const handleDelete = () => {
                    pushMessage({ text: i18n.t("Product removed") });
                    navigate(productListUrl());
                  };
                  const handleUpdate = () =>
                    pushMessage({ text: i18n.t("Saved changes") });
                  const handleImageCreate = () =>
                    pushMessage({
                      text: i18n.t("Image successfully uploaded")
                    });
                  const handleImageDeleteSuccess = () =>
                    pushMessage({
                      text: i18n.t("Image successfully deleted")
                    });
                  const handleVariantAdd = () =>
                    navigate(productVariantAddUrl(id));

                  const product = data ? data.product : undefined;
                  const allCollections =
                    data && data.collections
                      ? data.collections.edges.map(edge => edge.node)
                      : [];
                  const allCategories =
                    data && data.categories
                      ? data.categories.edges.map(edge => edge.node)
                      : [];
                  return (
                    <ProductUpdateOperations
                      product={product}
                      onDelete={handleDelete}
                      onImageCreate={handleImageCreate}
                      onImageDelete={handleImageDeleteSuccess}
                      onUpdate={handleUpdate}
                    >
                      {({
                        createProductImage,
                        deleteProduct,
                        deleteProductImage,
                        errors,
                        reorderProductImages,
                        updateProduct
                      }) => {
                        const handleImageDelete = (id: string) => () =>
                          deleteProductImage.mutate({ id });
                        const handleImageEdit = (imageId: string) => () =>
                          navigate(productImageUrl(id, imageId));
                        const handleSubmit = data => {
                          if (product) {
                            updateProduct.mutate({
                              attributes: data.attributes,
                              availableOn:
                                data.availableOn !== ""
                                  ? data.availableOn
                                  : null,
                              category: data.category,
                              chargeTaxes: data.chargeTaxes,
                              collections: data.collections,
                              description: data.description,
                              id: product.id,
                              isPublished: data.available,
                              name: data.name,
                              price: decimal(data.price)
                            });
                          }
                        };

                        const disableFormSave =
                          createProductImage.loading ||
                          deleteProduct.loading ||
                          reorderProductImages.loading ||
                          updateProduct.loading ||
                          loading;
                        const formTransitionState = getMutationState(
                          updateProduct.called,
                          updateProduct.loading,
                          maybe(() => updateProduct.data.productUpdate.errors)
                        );
                        return (
                          <>
                            <WindowTitle
                              title={maybe(() => data.product.name)}
                            />
                            <ProductUpdatePage
                              categories={allCategories}
                              collections={allCollections}
                              disabled={disableFormSave}
                              errors={errors}
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
                                  productTypeUrl(
                                    encodeURIComponent(
                                      data.product.productType.id
                                    )
                                  )
                                )
                              }
                              onBack={() => {
                                navigate(productListUrl());
                              }}
                              onDelete={() => navigate(productRemoveUrl(id))}
                              onProductShow={() => {
                                if (product) {
                                  window.open(product.url);
                                }
                              }}
                              onImageReorder={({ newIndex, oldIndex }) => {
                                if (product) {
                                  let ids = product.images.map(
                                    image => image.id
                                  );
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
                              onImageUpload={event => {
                                if (product) {
                                  createProductImage.mutate({
                                    alt: "",
                                    image: event.target.files[0],
                                    product: product.id
                                  });
                                }
                              }}
                              onImageEdit={handleImageEdit}
                              onImageDelete={handleImageDelete}
                            />
                            <Route
                              path={productRemovePath(":id")}
                              render={({ match }) => (
                                <ActionDialog
                                  open={!!match}
                                  onClose={() => navigate(productUrl(id))}
                                  onConfirm={() => deleteProduct.mutate({ id })}
                                  variant="delete"
                                  title={i18n.t("Remove product")}
                                >
                                  <DialogContentText
                                    dangerouslySetInnerHTML={{
                                      __html: i18n.t(
                                        "Are you sure you want to remove <strong>{{ name }}</strong>?",
                                        {
                                          name: product
                                            ? product.name
                                            : undefined
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
                    </ProductUpdateOperations>
                  );
                }}
              </TypedProductDetailsQuery>
            );
          }}
        </Navigator>
      );
    }}
  </Messages>
);
export default ProductUpdate;
