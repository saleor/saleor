import * as React from "react";

import {
  ProductDetailsQuery,
  ProductImageDeleteMutation,
  ProductImageDeleteMutationVariables
} from "../../gql-types";
import { productImagesDelete, TypedProductImagesDelete } from "../mutations";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import { productDetailsQuery } from "../queries";

interface ProductImagesDeleteProviderProps
  extends PartialMutationProviderProps<ProductImageDeleteMutation> {
  productId: string;
  imageId: string;
  children: PartialMutationProviderRenderProps<
    ProductImageDeleteMutation,
    ProductImageDeleteMutationVariables
  >;
}

const ProductImagesDeleteProvider: React.StatelessComponent<
  ProductImagesDeleteProviderProps
> = ({ productId, imageId, children, onError, onSuccess }) => (
  <TypedProductImagesDelete
    mutation={productImagesDelete}
    onCompleted={onSuccess}
    onError={onError}
    update={cache => {
      const data: ProductDetailsQuery = cache
        .readQuery({
          query: productDetailsQuery,
          variables: { id: productId }
        })
        .product.images.edges.filter(edge => edge.node.id !== imageId);
      cache.writeQuery({ query: productDetailsQuery, data });
    }}
  >
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedProductImagesDelete>
);

export default ProductImagesDeleteProvider;
