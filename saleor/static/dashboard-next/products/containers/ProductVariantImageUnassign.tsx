import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import {
  ProductVariantDetailsQuery,
  VariantImageUnassignMutation,
  VariantImageUnassignMutationVariables
} from "../../gql-types";
import {
  TypedVariantImageUnassign,
  variantImageUnassignMutation
} from "../mutations";
import { productVariantQuery } from "../queries";

interface VariantImageUnassignProviderProps
  extends PartialMutationProviderProps {
  id: string;
  children: PartialMutationProviderRenderProps<
    VariantImageUnassignMutation,
    VariantImageUnassignMutationVariables
  >;
}

const VariantImageUnassignProvider: React.StatelessComponent<
  VariantImageUnassignProviderProps
> = ({ id, children, onError, onSuccess }) => (
  <TypedVariantImageUnassign
    mutation={variantImageUnassignMutation}
    update={(cache, { data: { variantImageUnassign } }) => {
      if (variantImageUnassign.errors.length === 0) {
        const data: ProductVariantDetailsQuery = cache.readQuery({
          query: productVariantQuery,
          variables: { id }
        });
        data.productVariant.images.edges = data.productVariant.images.edges.filter(
          image => image.node.id !== variantImageUnassign.image.id
        );
        if (data.productVariant.images.edges.length === 0) {
          data.productVariant.product.variants.edges.filter(
            variant => variant.node.id === id
          )[0].node.image.edges = [];
        }
        cache.writeQuery({ query: productVariantQuery, data });
      }
    }}
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
  </TypedVariantImageUnassign>
);

export default VariantImageUnassignProvider;
