import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import {
  VariantUpdateMutation,
  VariantUpdateMutationVariables
} from "../../gql-types";
import { TypedVariantUpdateMutation } from "../mutations";

interface ProductVariantUpdateProviderProps
  extends PartialMutationProviderProps<VariantUpdateMutation> {
  children: PartialMutationProviderRenderProps<
    VariantUpdateMutation,
    VariantUpdateMutationVariables
  >;
}

const ProductVariantUpdateProvider: React.StatelessComponent<
  ProductVariantUpdateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedVariantUpdateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) => {
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedVariantUpdateMutation>
);
export default ProductVariantUpdateProvider;
