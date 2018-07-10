import * as React from "react";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import {
  ProductDetailsQuery,
  ProductUpdateMutation,
  ProductUpdateMutationVariables
} from "../../gql-types";
import {
  productUpdateMutation,
  TypedProductUpdateMutation
} from "../mutations";
import { productDetailsQuery } from "../queries";

interface ProductUpdateProviderProps
  extends PartialMutationProviderProps<ProductUpdateMutation> {
  productId: string;
  children: ((
    props: PartialMutationProviderRenderProps<
      ProductUpdateMutation,
      ProductUpdateMutationVariables
    >
  ) => React.ReactElement<any>);
}

const ProductUpdateProvider: React.StatelessComponent<
  ProductUpdateProviderProps
> = ({ productId, children, onError, onSuccess }) => (
  <TypedProductUpdateMutation
    mutation={productUpdateMutation}
    onCompleted={onSuccess}
    onError={onError}
    update={(cache, { data: { productUpdate } }) => {
      const data: ProductDetailsQuery = cache.readQuery({
        query: productDetailsQuery,
        variables: { id: productId }
      });
      data.product = productUpdate.product;
      cache.writeQuery({ query: productDetailsQuery, data });
    }}
  >
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
