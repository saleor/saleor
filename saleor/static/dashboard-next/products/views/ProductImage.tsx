import * as React from "react";

import { productImageUrl, productUrl } from "..";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import ProductImagePage from "../components/ProductImagePage";
import {
  TypedProductImageDeleteMutation,
  TypedProductImageUpdateMutation
} from "../mutations";
import { productImageQuery, TypedProductImageQuery } from "../queries";
import { ProductImageUpdate } from "../types/ProductImageUpdate";

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
            navigate(productUrl(decodeURIComponent(productId)));
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
              query={productImageQuery}
              variables={{
                imageId,
                productId
              }}
              fetchPolicy="cache-and-network"
            >
              {({ data, loading }) => {
                return (
                  <TypedProductImageUpdateMutation
                    onCompleted={handleUpdateSuccess}
                  >
                    {updateImage => (
                      <TypedProductImageDeleteMutation onCompleted={handleBack}>
                        {deleteImage => {
                          const handleDelete = () =>
                            deleteImage({ variables: { id: imageId } });
                          const handleImageClick = (id: string) => () =>
                            navigate(
                              productImageUrl(
                                decodeURIComponent(productId),
                                decodeURIComponent(id)
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
                          return (
                            <ProductImagePage
                              disabled={loading}
                              image={image || null}
                              images={
                                data &&
                                data.product &&
                                data.product.images &&
                                data.product.images.edges
                                  ? data.product.images.edges.map(
                                      edge => edge.node
                                    )
                                  : undefined
                              }
                              onBack={handleBack}
                              onDelete={handleDelete}
                              onRowClick={handleImageClick}
                              onSubmit={handleUpdate}
                            />
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
