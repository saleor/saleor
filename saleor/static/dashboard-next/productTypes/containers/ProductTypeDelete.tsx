import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import { TypedProductTypeDeleteMutation } from "../mutations";
import {
  ProductTypeDelete,
  ProductTypeDeleteVariables
} from "../types/ProductTypeDelete";

interface ProductTypeDeleteProviderProps extends PartialMutationProviderProps {
  id: string;
  children: PartialMutationProviderRenderProps<
    ProductTypeDelete,
    ProductTypeDeleteVariables
  >;
}

const ProductTypeDeleteProvider: React.StatelessComponent<
  ProductTypeDeleteProviderProps
> = ({ id, children, onError, onSuccess }) => (
  <TypedProductTypeDeleteMutation
    variables={{ id }}
    onCompleted={onSuccess}
    onError={onError}
  >
    {(mutate, { data, loading, error }) => {
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedProductTypeDeleteMutation>
);

export default ProductTypeDeleteProvider;
