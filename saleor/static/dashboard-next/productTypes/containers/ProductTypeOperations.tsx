import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../..";
import {
  ProductTypeDeleteMutation,
  ProductTypeDeleteMutationVariables,
  ProductTypeUpdateMutation,
  ProductTypeUpdateMutationVariables
} from "../../gql-types";
import ProductTypeDeleteProvider from "./ProductTypeDelete";
import ProductTypeUpdateProvider from "./ProductTypeUpdate";

interface ProductTypeOperationsProps extends MutationProviderProps {
  id: string;
  children: MutationProviderRenderProps<{
    deleteProductType: PartialMutationProviderOutput<
      ProductTypeDeleteMutation,
      ProductTypeDeleteMutationVariables
    >;
    updateProductType: PartialMutationProviderOutput<
      ProductTypeUpdateMutation,
      ProductTypeUpdateMutationVariables
    >;
    loading: boolean;
  }>;
  onDelete?: (data: ProductTypeDeleteMutation) => void;
  onUpdate?: (data: ProductTypeUpdateMutation) => void;
}

const ProductTypeOperations: React.StatelessComponent<
  ProductTypeOperationsProps
> = ({ id, children, onError, onDelete, onUpdate }) => {
  return (
    <ProductTypeDeleteProvider id={id} onError={onError} onSuccess={onDelete}>
      {deleteProductType => (
        <ProductTypeUpdateProvider onError={onError} onSuccess={onUpdate}>
          {updateProductType =>
            children({
              deleteProductType: {
                data: deleteProductType.data,
                loading: deleteProductType.loading,
                mutate: () => deleteProductType.mutate({ variables: { id } })
              },
              errors: [],
              loading: deleteProductType.loading,
              updateProductType: {
                data: updateProductType.data,
                loading: updateProductType.loading,
                mutate: variables => updateProductType.mutate({ variables })
              }
            })
          }
        </ProductTypeUpdateProvider>
      )}
    </ProductTypeDeleteProvider>
  );
};
export default ProductTypeOperations;
