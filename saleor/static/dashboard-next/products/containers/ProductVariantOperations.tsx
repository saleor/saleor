import * as React from "react";

import { VariantUpdateMutationVariables } from "../../gql-types";
import VariantDeleteProvider from "./ProductVariantDelete";
import VariantUpdateProvider from "./ProductVariantUpdate";

interface VariantDeleteOperationsProps {
  productId: string;
  variantId: string;
  children: (
    mutations: {
      deleteVariant(): void;
      updateVariant(variables: VariantUpdateMutationVariables): void;
    }
  ) => React.ReactElement<any>;
}

const VariantDeleteOperations: React.StatelessComponent<
  VariantDeleteOperationsProps
> = ({ productId, variantId, children }) => {
  return (
    <VariantUpdateProvider variantId={variantId}>
      {updateVariant => (
        <VariantDeleteProvider productId={productId} variantId={variantId}>
          {deleteVariant =>
            children({
              deleteVariant,
              updateVariant: variables => updateVariant({ variables })
            })
          }
        </VariantDeleteProvider>
      )}
    </VariantUpdateProvider>
  );
};
export default VariantDeleteOperations;
