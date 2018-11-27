import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";
import { Route } from "react-router-dom";

import ActionDialog from "../../../components/ActionDialog";
import Messages from "../../../components/messages";
import Navigator from "../../../components/Navigator";
import i18n from "../../../i18n";
import { getMutationState, maybe } from "../../../misc";
import ProductImagePage from "../../components/ProductImagePage";
import {
  TypedProductImageDeleteMutation,
  TypedProductImageUpdateMutation
} from "../../mutations";
import { TypedProductImageQuery } from "../../queries";
import { ProductImageUpdate } from "../../types/ProductImageUpdate";
import { productImageUrl, productUrl } from "../../urls";
import { productImageRemoveUrl } from "./urls";

interface ProductImageProps {
  imageId: string;
  productId: string;
}

export const ProductImage: React.StatelessComponent<ProductImageProps> = ({
  imageId,
  productId
}) => (
  <Messages>
    {pushMessage => (
      <Navigator>
        {navigate => {
          const handleBack = () =>
            navigate(productUrl(encodeURIComponent(productId)));
          const handleUpdateSuccess = (data: ProductImageUpdate) => {
            if (
              data.productImageUpdate &&
              data.productImageUpdate.errors.length === 0
            ) {
              pushMessage({ text: "Saved changes" });
            }
          };
          return (
            <TypedProductImageQuery
              displayLoader
              variables={{
                imageId,
                productId
              }}
            >
              {({ data, loading }) => {
                return (
                  <TypedProductImageUpdateMutation
                    onCompleted={handleUpdateSuccess}
                  >
                    {(updateImage, updateResult) => (
                      <TypedProductImageDeleteMutation onCompleted={handleBack}>
                        {deleteImage => {
                          const handleDelete = () =>
                            deleteImage({ variables: { id: imageId } });
                          const handleImageClick = (id: string) => () =>
                            navigate(
                              productImageUrl(
                                encodeURIComponent(productId),
                                encodeURIComponent(id)
                              )
                            );
                          const handleUpdate = (formData: {
                            description: string;
                          }) => {
                            updateImage({
                              variables: {
                                alt: formData.description,
                                id: imageId
                              }
                            });
                          };
                          const image =
                            data && data.product && data.product.mainImage;

                          const formTransitionState = getMutationState(
                            updateResult.called,
                            updateResult.loading,
                            maybe(
                              () => updateResult.data.productImageUpdate.errors
                            )
                          );
                          return (
                            <>
                              <ProductImagePage
                                disabled={loading}
                                image={image || null}
                                images={maybe(() => data.product.images)}
                                onBack={handleBack}
                                onDelete={() =>
                                  navigate(
                                    productImageRemoveUrl(
                                      encodeURIComponent(productId),
                                      encodeURIComponent(imageId)
                                    )
                                  )
                                }
                                onRowClick={handleImageClick}
                                onSubmit={handleUpdate}
                                saveButtonBarState={formTransitionState}
                              />
                              <Route
                                path={productImageRemoveUrl(
                                  ":productId",
                                  ":imageId"
                                )}
                                render={({ match }) => (
                                  <ActionDialog
                                    onClose={() =>
                                      navigate(
                                        productImageUrl(productId, imageId)
                                      )
                                    }
                                    onConfirm={handleDelete}
                                    open={!!match}
                                    title={i18n.t("Remove image", {
                                      context: "modal title"
                                    })}
                                    variant="delete"
                                  >
                                    <DialogContentText>
                                      {i18n.t(
                                        "Are you sure you want o remove this image?",
                                        {
                                          context: "modal content"
                                        }
                                      )}
                                    </DialogContentText>
                                  </ActionDialog>
                                )}
                              />
                            </>
                          );
                        }}
                      </TypedProductImageDeleteMutation>
                    )}
                  </TypedProductImageUpdateMutation>
                );
              }}
            </TypedProductImageQuery>
          );
        }}
      </Navigator>
    )}
  </Messages>
);
export default ProductImage;
