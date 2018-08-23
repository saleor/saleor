import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../..";
import {
  ProductTypeDeleteMutation,
  ProductTypeDeleteMutationVariables
} from "../../gql-types";
import ProductTypeDeleteProvider from "./ProductTypeDelete";

interface ProductTypeOperationsProps extends MutationProviderProps {
  id: string;
  children: MutationProviderRenderProps<{
    deleteProductType: PartialMutationProviderOutput<
      ProductTypeDeleteMutation,
      ProductTypeDeleteMutationVariables
    >;
    loading: boolean;
  }>;
  onDelete?: (data: ProductTypeDeleteMutation) => void;
}

const ProductTypeOperations: React.StatelessComponent<
  ProductTypeOperationsProps
> = ({ id, children, onError, onDelete }) => {
  return (
    <ProductTypeDeleteProvider id={id} onError={onError} onSuccess={onDelete}>
      {deleteProductType =>
        children({
          deleteProductType: {
            data: deleteProductType.data,
            loading: deleteProductType.loading,
            mutate: () => deleteProductType.mutate({ variables: { id } })
          },
          errors: [],
          loading: deleteProductType.loading
        })
      }
    </ProductTypeDeleteProvider>
  );
};
export default ProductTypeOperations;
