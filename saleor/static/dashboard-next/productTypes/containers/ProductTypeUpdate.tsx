import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import { TypedProductTypeUpdateMutation } from "../mutations";
import {
  ProductTypeUpdate,
  ProductTypeUpdateVariables
} from "../types/ProductTypeUpdate";

interface ProductTypeUpdateProviderProps extends PartialMutationProviderProps {
  children: PartialMutationProviderRenderProps<
    ProductTypeUpdate,
    ProductTypeUpdateVariables
  >;
}

const ProductTypeUpdateProvider: React.StatelessComponent<
  ProductTypeUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedProductTypeUpdateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, loading, error }) => {
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedProductTypeUpdateMutation>
);

export default ProductTypeUpdateProvider;
