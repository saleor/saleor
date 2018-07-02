import * as React from "react";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import { ProductVariantDetailsQuery } from "../../gql-types";
import {
  TypedVariantUpdateMutation,
  variantUpdateMutation
} from "../mutations";
import { productVariantQuery } from "../queries";

interface ProductVariantUpdateProviderProps {
  children: any;
  variantId: string;
}

const ProductVariantUpdateProvider: React.StatelessComponent<
  ProductVariantUpdateProviderProps
> = ({ variantId, children }) => (
  <TypedVariantUpdateMutation
    mutation={variantUpdateMutation}
    update={(cache, { data: { productVariantUpdate } }) => {
      const data: ProductVariantDetailsQuery = cache.readQuery({
        query: productVariantQuery,
        variables: { id: variantId }
      });
      data.productVariant = productVariantUpdate.productVariant;
      cache.writeQuery({ query: productVariantQuery, data });
    }}
  >
    {(updateVariant, { error }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children(updateVariant);
    }}
  </TypedVariantUpdateMutation>
);
export default ProductVariantUpdateProvider;
