import * as React from "react";

import { MutationProviderProps, MutationProviderRenderProps } from "../..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
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
  extends MutationProviderProps<ProductUpdateMutation> {
  productId: string;
  children: ((
    props: MutationProviderRenderProps<
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
    {(mutate, { data, error, loading }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedProductUpdateMutation>
);

export default ProductUpdateProvider;
