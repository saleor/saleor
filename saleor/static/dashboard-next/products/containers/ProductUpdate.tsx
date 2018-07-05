import * as React from "react";

import { MutationProviderChildrenRenderProps } from "../..";
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

interface ProductUpdateProviderProps {
  productId: string;
  children: ((
    props: MutationProviderChildrenRenderProps<
      ProductUpdateMutation,
      ProductUpdateMutationVariables
    >
  ) => React.ReactElement<any>);
}

const ProductUpdateProvider: React.StatelessComponent<
  ProductUpdateProviderProps
> = ({ productId, children }) => (
  <TypedProductUpdateMutation
    mutation={productUpdateMutation}
    update={(cache, { data: { productUpdate } }) => {
      const data: ProductDetailsQuery = cache.readQuery({
        query: productDetailsQuery,
        variables: { id: productId }
      });
      data.product = productUpdate.product;
      cache.writeQuery({ query: productDetailsQuery, data });
    }}
  >
    {(mutate, { called, error, loading }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children({
        called,
        error,
        loading,
        mutate
      });
    }}
  </TypedProductUpdateMutation>
);

export default ProductUpdateProvider;
