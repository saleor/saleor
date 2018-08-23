import * as React from "react";

import {
  ProductImageDeleteMutation,
  ProductImageDeleteMutationVariables
} from "../../gql-types";
import { TypedProductImageDeleteMutation } from "../mutations";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";

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
  <TypedProductImageDeleteMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedProductImageDeleteMutation>
);

export default ProductImagesDeleteProvider;
