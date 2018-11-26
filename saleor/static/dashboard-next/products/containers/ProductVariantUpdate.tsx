import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import { TypedVariantUpdateMutation } from "../mutations";
import { VariantUpdate, VariantUpdateVariables } from "../types/VariantUpdate";

interface ProductVariantUpdateProviderProps
  extends PartialMutationProviderProps<VariantUpdate> {
  children: PartialMutationProviderRenderProps<
    VariantUpdate,
    VariantUpdateVariables
  >;
}

const ProductVariantUpdateProvider: React.StatelessComponent<
  ProductVariantUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedVariantUpdateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { called, data, error, loading }) => {
      return children({
        called,
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedVariantUpdateMutation>
);
export default ProductVariantUpdateProvider;
