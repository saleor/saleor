import * as React from "react";

import {
  ProductImageUpdateMutation,
  ProductImageUpdateMutationVariables
} from "../../gql-types";
import { TypedProductImageUpdateMutation } from "../mutations";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

interface ProductImagesUpdateProviderProps
  extends PartialMutationProviderProps<ProductImageUpdateMutation> {
  productId: string;
  imageId: string;
  children: PartialMutationProviderRenderProps<
    ProductImageUpdateMutation,
    ProductImageUpdateMutationVariables
  >;
}

const ProductImagesUpdateProvider: React.StatelessComponent<
  ProductImagesUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedProductImageUpdateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedProductImageUpdateMutation>
);

export default ProductImagesUpdateProvider;
