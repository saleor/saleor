import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import {
  ProductVariantDetailsQuery,
  VariantImageAssignMutation,
  VariantImageAssignMutationVariables
} from "../../gql-types";
import {
  TypedVariantImageAssign,
  variantImageAssignMutation
} from "../mutations";
import { productVariantQuery } from "../queries";

interface VariantImageAssignProviderProps extends PartialMutationProviderProps {
  id: string;
  children: PartialMutationProviderRenderProps<
    VariantImageAssignMutation,
    VariantImageAssignMutationVariables
  >;
}

const VariantImageAssignProvider: React.StatelessComponent<
  VariantImageAssignProviderProps
> = ({ id, children, onError, onSuccess }) => (
  <TypedVariantImageAssign
    mutation={variantImageAssignMutation}
    update={(cache, { data: { variantImageAssign } }) => {
      if (variantImageAssign.errors.length === 0) {
        const data: ProductVariantDetailsQuery = cache.readQuery({
          query: productVariantQuery,
          variables: { id }
        });
        data.productVariant.images.edges = [
          ...data.productVariant.images.edges,
          {
            __typename: "ProductImageCountableEdge",
            node: {
              __typename: "ProductImage",
              id: variantImageAssign.image.id
            }
          } as any
        ];
        if (data.productVariant.images.edges.length === 1) {
          data.productVariant.product.variants.edges.filter(
            variant => variant.node.id === id
          )[0].node.image.edges = [
            ...data.productVariant.images.edges,
            {
              __typename: "ProductImageCountableEdge",
              node: {
                __typename: "ProductImage",
                id: variantImageAssign.image.id
              }
            } as any
          ];
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
  </TypedVariantImageAssign>
);

export default VariantImageAssignProvider;
