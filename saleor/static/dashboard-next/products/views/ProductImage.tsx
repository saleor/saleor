import * as React from "react";

import { productImageUrl, productUrl } from "..";
import Navigator from "../../components/Navigator";
import { createPaginationData, createPaginationState } from "../../misc";
import ProductImagePage from "../components/ProductImagePage";
import {
  productImageDeleteMutation,
  TypedProductImageDeleteMutation
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
  <Navigator>
    {navigate => {
      const handleBack = () => navigate(productUrl(productId));
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedProductImageQuery
          query={productImageQuery}
          variables={{
            imageAfter: paginationState.after,
            imageBefore: paginationState.before,
            imageId,
            productId
          }}
          fetchPolicy="cache-and-network"
        >
          {({ data, loading }) => {
            return (
              <TypedProductImageDeleteMutation
                mutation={productImageDeleteMutation}
                onCompleted={handleBack}
              >
                {mutate => {
                  const handleDelete = () =>
                    mutate({ variables: { id: imageId } });
                  const {
                    loadNextPage,
                    loadPreviousPage,
                    pageInfo
                  } = createPaginationData(
                    navigate,
                    paginationState,
                    productImageUrl(productId, imageId),
                    data && data.product && data.product.images
                      ? data.product.images.pageInfo
                      : undefined,
                    loading
                  );
                  const handleImageClick = (id: string) => () =>
                    navigate(productImageUrl(productId, id));
                  const image =
                    data &&
                    data.product &&
                    data.product.image &&
                    data.product.image.edges &&
                    data.product.image.edges[0] &&
                    data.product.image.edges[0]
                      ? data.product.image.edges[0].node
                      : undefined;
                  return (
                    <ProductImagePage
                      description={image ? image.alt : null}
                      // TODO: unlock editing after API fixes
                      disabled={true}
                      image={image || null}
                      images={
                        data &&
                        data.product &&
                        data.product.images &&
                        data.product.images.edges
                          ? data.product.images.edges.map(edge => edge.node)
                          : undefined
                      }
                      pageInfo={pageInfo}
                      onBack={handleBack}
                      onDelete={handleDelete}
                      onNextPage={loadNextPage}
                      onPreviousPage={loadPreviousPage}
                      onRowClick={handleImageClick}
                      onSubmit={() => {}}
                    />
                  );
                }}
              </TypedProductImageDeleteMutation>
            );
          }}
        </TypedProductImageQuery>
      );
    }}
  </Navigator>
);
export default ProductImage;
