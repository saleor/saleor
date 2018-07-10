import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import {
  ProductDetailsQuery,
  ProductImageReorderMutation,
  ProductImageReorderMutationVariables
} from "../../gql-types";
import { productImagesReorder, TypedProductImagesReorder } from "../mutations";

import { MutationProviderProps, MutationProviderRenderProps } from "../..";
import { productDetailsQuery } from "../queries";

interface ProductImagesReorderProviderProps
  extends MutationProviderProps<ProductImageReorderMutation> {
  productId: string;
  children: ((
    props: MutationProviderRenderProps<
      ProductImageReorderMutation,
      ProductImageReorderMutationVariables
    >
  ) => React.ReactElement<any>);
}

const ProductImagesReorderProvider: React.StatelessComponent<
  ProductImagesReorderProviderProps
> = ({ productId, children, onError, onSuccess }) => (
  <TypedProductImagesReorder
    mutation={productImagesReorder}
    onCompleted={onSuccess}
    onError={onError}
    update={(cache, { data: { productImageReorder } }) => {
      const data: ProductDetailsQuery = cache.readQuery({
        query: productDetailsQuery,
        variables: { id: productId }
      });
      data.product.images.edges.forEach((item, index, array) => {
        array[index].node = productImageReorder.productImages[index];
      });
      cache.writeQuery({ query: productDetailsQuery, data });
    }}
  >
    {(mutate, { data, error, loading }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedProductImagesReorder>
);

export default ProductImagesReorderProvider;
