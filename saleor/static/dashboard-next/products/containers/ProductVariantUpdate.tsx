import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import {
  ProductVariantDetailsQuery,
  VariantUpdateMutation,
  VariantUpdateMutationVariables
} from "../../gql-types";
import {
  TypedVariantUpdateMutation,
  variantUpdateMutation
} from "../mutations";
import { productVariantQuery } from "../queries";

interface ProductVariantUpdateProviderProps
  extends PartialMutationProviderProps<VariantUpdateMutation> {
  children: PartialMutationProviderRenderProps<
    VariantUpdateMutation,
    VariantUpdateMutationVariables
  >;
  id: string;
}

const ProductVariantUpdateProvider: React.StatelessComponent<
  ProductVariantUpdateProviderProps
> = ({ id, children, onError, onSuccess }) => (
  <TypedVariantUpdateMutation
    mutation={variantUpdateMutation}
    update={(cache, { data: { productVariantUpdate } }) => {
      const data: ProductVariantDetailsQuery = cache.readQuery({
        query: productVariantQuery,
        variables: { id }
      });
      data.productVariant = productVariantUpdate.productVariant;
      cache.writeQuery({ query: productVariantQuery, data });
    }}
    onCompleted={onSuccess}
    onError={onError}
  >
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
