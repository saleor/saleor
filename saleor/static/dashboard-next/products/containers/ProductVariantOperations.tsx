import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../..";
import {
  VariantDeleteMutation,
  VariantImageAssignMutation,
  VariantImageAssignMutationVariables,
  VariantImageUnassignMutation,
  VariantImageUnassignMutationVariables,
  VariantUpdateMutation,
  VariantUpdateMutationVariables
} from "../../gql-types";
import VariantDeleteProvider from "./ProductVariantDelete";
import VariantImageAssignProvider from "./ProductVariantImageAssign";
import VariantImageUnassignProvider from "./ProductVariantImageUnassign";
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
    assignImage: PartialMutationProviderOutput<
      VariantImageAssignMutation,
      VariantImageAssignMutationVariables
    >;
    unassignImage: PartialMutationProviderOutput<
      VariantImageUnassignMutation,
      VariantImageUnassignMutationVariables
    >;
  }>;
  onDelete?: (data: VariantDeleteMutation) => void;
  onImageAssign?: (data: VariantImageAssignMutation) => void;
  onImageUnassign?: (data: VariantImageUnassignMutation) => void;
  onUpdate?: (data: VariantUpdateMutation) => void;
}

const VariantUpdateOperations: React.StatelessComponent<
  VariantDeleteOperationsProps
> = ({ id, children, onError, onDelete, onUpdate }) => {
  return (
    <VariantImageAssignProvider>
      {assignImage => (
        <VariantImageUnassignProvider>
          {unassignImage => (
            <VariantUpdateProvider onError={onError} onSuccess={onUpdate}>
              {updateVariant => (
                <VariantDeleteProvider
                  id={id}
                  onError={onError}
                  onSuccess={onDelete}
                >
                  {deleteVariant =>
                    children({
                      assignImage: {
                        data: assignImage.data,
                        loading: assignImage.loading,
                        mutate: variables => assignImage.mutate({ variables })
                      },
                      deleteVariant: {
                        data: deleteVariant.data,
                        loading: deleteVariant.loading,
                        mutate: () =>
                          deleteVariant.mutate({ variables: { id } })
                      },
                      errors:
                        updateVariant &&
                        updateVariant.data &&
                        updateVariant.data.productVariantUpdate &&
                        updateVariant.data.productVariantUpdate.errors
                          ? updateVariant.data.productVariantUpdate.errors
                          : [],
                      unassignImage: {
                        data: unassignImage.data,
                        loading: unassignImage.loading,
                        mutate: variables => unassignImage.mutate({ variables })
                      },
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
          )}
        </VariantImageUnassignProvider>
      )}
    </VariantImageAssignProvider>
  );
};
export default VariantUpdateOperations;
