import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import {
  ProductDetailsQuery,
  ProductImageReorderMutation,
  ProductImageReorderMutationVariables
} from "../../gql-types";
import { productImagesReorder, TypedProductImagesReorder } from "../mutations";

import { MutationProviderChildrenRenderProps } from "../..";
import { productDetailsQuery } from "../queries";

interface ProductImagesReorderProviderProps {
  productId: string;
  children: ((
    props: MutationProviderChildrenRenderProps<
      ProductImageReorderMutation,
      ProductImageReorderMutationVariables
    >
  ) => React.ReactElement<any>);
}

const ProductImagesReorderProvider: React.StatelessComponent<
  ProductImagesReorderProviderProps
> = ({ productId, children }) => (
  <TypedProductImagesReorder
    mutation={productImagesReorder}
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
    {(mutate, { called, error, loading }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children({
        called,
        error,
        loading,
        mutate
      });
    }}
  </TypedProductImagesReorder>
);

export default ProductImagesReorderProvider;
