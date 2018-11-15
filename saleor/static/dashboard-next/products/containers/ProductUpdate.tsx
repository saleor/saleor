import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import { TypedProductUpdateMutation } from "../mutations";
import { ProductUpdate, ProductUpdateVariables } from "../types/ProductUpdate";

interface ProductUpdateProviderProps
  extends PartialMutationProviderProps<ProductUpdate> {
  children: PartialMutationProviderRenderProps<
    ProductUpdate,
    ProductUpdateVariables
  >;
}

const ProductUpdateProvider: React.StatelessComponent<
  ProductUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedProductUpdateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedProductUpdateMutation>
);

export default ProductUpdateProvider;
