import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../..";
import {
  ProductTypeDelete,
  ProductTypeDeleteVariables
} from "../types/ProductTypeDelete";
import {
  ProductTypeUpdate,
  ProductTypeUpdateVariables
} from "../types/ProductTypeUpdate";
import ProductTypeDeleteProvider from "./ProductTypeDelete";
import ProductTypeUpdateProvider from "./ProductTypeUpdate";

interface ProductTypeOperationsProps extends MutationProviderProps {
  id: string;
  children: MutationProviderRenderProps<{
    deleteProductType: PartialMutationProviderOutput<
      ProductTypeDelete,
      ProductTypeDeleteVariables
    >;
    updateProductType: PartialMutationProviderOutput<
      ProductTypeUpdate,
      ProductTypeUpdateVariables
    >;
    loading: boolean;
  }>;
  onDelete?: (data: ProductTypeDelete) => void;
  onUpdate?: (data: ProductTypeUpdate) => void;
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
