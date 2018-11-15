import * as React from "react";

import { TypedProductImageDeleteMutation } from "../mutations";
import {
  ProductImageDelete,
  ProductImageDeleteVariables
} from "../types/ProductImageDelete";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface ProductImagesDeleteProviderProps
  extends PartialMutationProviderProps<ProductImageDelete> {
  productId: string;
  imageId: string;
  children: PartialMutationProviderRenderProps<
    ProductImageDelete,
    ProductImageDeleteVariables
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
