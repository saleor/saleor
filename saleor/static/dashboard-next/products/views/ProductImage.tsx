import * as React from "react";

import { productImageUrl, productUrl } from "..";
import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { ProductImageUpdateMutation } from "../../gql-types";
import { createPaginationData, createPaginationState } from "../../misc";
import ProductImagePage from "../components/ProductImagePage";
import {
  productImageDeleteMutation,
  productImageUpdateMutation,
  TypedProductImageDeleteMutation,
  TypedProductImageUpdateMutation
} from "../mutations";
import { productImageQuery, TypedProductImageQuery } from "../queries";

interface ProductImageProps {
  imageId: string;
  productId: string;
  params: {
    after?: string;
    before?: string;
  };
}

const PAGINATE_BY = 8;

export const ProductImage: React.StatelessComponent<ProductImageProps> = ({
  imageId,
  params,
  productId
}) => (
  <Messages>
    {pushMessage => (
      <Navigator>
        {navigate => {
          const handleBack = () => navigate(productUrl(productId));
          const handleUpdateSuccess = (data: ProductImageUpdateMutation) => {
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
                    mutation={productImageUpdateMutation}
                    onCompleted={handleUpdateSuccess}
                  >
                    {updateImage => (
                      <TypedProductImageDeleteMutation
                        mutation={productImageDeleteMutation}
                        onCompleted={handleBack}
                      >
                        {deleteImage => {
                          const handleDelete = () =>
                            deleteImage({ variables: { id: imageId } });
                          const handleImageClick = (id: string) => () =>
                            navigate(productImageUrl(productId, id));
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
                            data && data.product && data.product.image;
                          return (
                            <ProductImagePage
                              description={image ? image.alt : null}
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
