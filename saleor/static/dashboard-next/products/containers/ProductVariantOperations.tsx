import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../..";
import {
  VariantDeleteMutation,
  VariantUpdateMutation,
  VariantUpdateMutationVariables
} from "../../gql-types";
import VariantDeleteProvider from "./ProductVariantDelete";
import VariantUpdateProvider from "./ProductVariantUpdate";

interface VariantDeleteOperationsProps extends MutationProviderProps {
  productId: string;
  id: string;
  children: MutationProviderRenderProps<{
    deleteVariant: PartialMutationProviderOutput;
    updateVariant: PartialMutationProviderOutput<
      VariantUpdateMutation,
      VariantUpdateMutationVariables
    >;
  }>;
  onDelete?: (data: VariantDeleteMutation) => void;
  onUpdate?: (data: VariantUpdateMutation) => void;
}

const VariantDeleteOperations: React.StatelessComponent<
  VariantDeleteOperationsProps
> = ({ id, children, onError, onDelete, onUpdate }) => {
  return (
    <VariantUpdateProvider id={id} onError={onError} onSuccess={onUpdate}>
      {updateVariant => (
        <VariantDeleteProvider id={id} onError={onError} onSuccess={onDelete}>
          {deleteVariant =>
            children({
              deleteVariant: {
                data: deleteVariant.data,
                loading: deleteVariant.loading,
                mutate: variables => deleteVariant.mutate({ variables: { id } })
              },
              errors:
                updateVariant &&
                updateVariant.data &&
                updateVariant.data.productVariantUpdate &&
                updateVariant.data.productVariantUpdate.errors
                  ? updateVariant.data.productVariantUpdate.errors
                  : [],
              updateVariant: {
                data: updateVariant.data,
                loading: updateVariant.loading,
                mutate: variables => updateVariant.mutate({ variables })
              }
            })
          }
        </VariantDeleteProvider>
      )}
    </VariantUpdateProvider>
  );
};
export default VariantDeleteOperations;
