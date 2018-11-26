import * as React from "react";

import { TypedProductImageUpdateMutation } from "../mutations";
import {
  ProductImageUpdate,
  ProductImageUpdateVariables
} from "../types/ProductImageUpdate";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface ProductImagesUpdateProviderProps
  extends PartialMutationProviderProps<ProductImageUpdate> {
  productId: string;
  imageId: string;
  children: PartialMutationProviderRenderProps<
    ProductImageUpdate,
    ProductImageUpdateVariables
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
