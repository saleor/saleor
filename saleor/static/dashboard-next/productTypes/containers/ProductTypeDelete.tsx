import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import {
  ProductTypeDeleteMutation,
  ProductTypeDeleteMutationVariables
} from "../../gql-types";
import {
  productTypeDeleteMutation,
  TypedProductTypeDeleteMutation
} from "../mutations";

interface ProductTypeDeleteProviderProps extends PartialMutationProviderProps {
  id: string;
  children: PartialMutationProviderRenderProps<
    ProductTypeDeleteMutation,
    ProductTypeDeleteMutationVariables
  >;
}

const ProductTypeDeleteProvider: React.StatelessComponent<
  ProductTypeDeleteProviderProps
> = ({ id, children, onError, onSuccess }) => (
  <TypedProductTypeDeleteMutation
    mutation={productTypeDeleteMutation}
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
