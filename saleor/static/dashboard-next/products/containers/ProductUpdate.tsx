import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import { ProductDetailsQuery } from "../../gql-types";
import {
  productUpdateMutation,
  TypedProductUpdateMutation,
} from "../mutations";
import { productDetailsQuery } from "../queries";

interface ProductUpdateProviderProps {
  productId: string;
  children: any;
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
    {(updateProduct, { error }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children(updateProduct);
    }}
  </TypedProductUpdateMutation>
);

export default ProductUpdateProvider;
