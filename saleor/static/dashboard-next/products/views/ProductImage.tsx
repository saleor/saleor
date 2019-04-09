import DialogContentText from "@material-ui/core/DialogContentText";
import * as React from "react";

import ActionDialog from "../../components/ActionDialog";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import ProductImagePage from "../components/ProductImagePage";
import {
  TypedProductImageDeleteMutation,
  TypedProductImageUpdateMutation
} from "../mutations";
import { TypedProductImageQuery } from "../queries";
import { ProductImageUpdate } from "../types/ProductImageUpdate";
import {
  productImageUrl,
  ProductImageUrlQueryParams,
  productUrl
} from "../urls";

interface ProductImageProps {
  imageId: string;
  productId: string;
  params: ProductImageUrlQueryParams;
}

export const ProductImage: React.StatelessComponent<ProductImageProps> = ({
  imageId,
  productId,
  params
}) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const handleBack = () => navigate(productUrl(productId));
  const handleUpdateSuccess = (data: ProductImageUpdate) => {
    if (data.productImageUpdate.errors.length === 0) {
      notify({ text: "Saved changes" });
    }
  };
  return (
    <TypedProductImageQuery
      displayLoader
      variables={{
        imageId,
        productId
      }}
      require={["product"]}
    >
      {({ data, loading }) => {
        return (
          <TypedProductImageUpdateMutation onCompleted={handleUpdateSuccess}>
            {(updateImage, updateResult) => (
              <TypedProductImageDeleteMutation onCompleted={handleBack}>
                {(deleteImage, deleteResult) => {
                  const handleDelete = () =>
                    deleteImage({ variables: { id: imageId } });
                  const handleImageClick = (id: string) => () =>
                    navigate(productImageUrl(productId, id));
                  const handleUpdate = (formData: { description: string }) => {
                    updateImage({
                      variables: {
                        alt: formData.description,
                        id: imageId
                      }
                    });
                  };
                  const image = data && data.product && data.product.mainImage;

                  const formTransitionState = getMutationState(
                    updateResult.called,
                    updateResult.loading,
                    maybe(() => updateResult.data.productImageUpdate.errors)
                  );
                  const deleteTransitionState = getMutationState(
                    deleteResult.called,
                    deleteResult.loading,
                    []
                  );
                  return (
                    <>
                      <ProductImagePage
                        disabled={loading}
                        product={maybe(() => data.product.name)}
                        image={image || null}
                        images={maybe(() => data.product.images)}
                        onBack={handleBack}
                        onDelete={() =>
                          navigate(
                            productImageUrl(productId, imageId, {
                              action: "remove"
                            })
                          )
                        }
                        onRowClick={handleImageClick}
                        onSubmit={handleUpdate}
                        saveButtonBarState={formTransitionState}
                      />
                      <ActionDialog
                        onClose={() =>
                          navigate(productImageUrl(productId, imageId), true)
                        }
                        onConfirm={handleDelete}
                        open={params.action === "remove"}
                        title={i18n.t("Remove image", {
                          context: "modal title"
                        })}
                        variant="delete"
                        confirmButtonState={deleteTransitionState}
                      >
                        <DialogContentText>
                          {i18n.t(
                            "Are you sure you want to remove this image?",
                            {
                              context: "modal content"
                            }
                          )}
                        </DialogContentText>
                      </ActionDialog>
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
};
export default ProductImage;
