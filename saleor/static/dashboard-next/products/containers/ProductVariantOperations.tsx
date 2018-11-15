import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../../types";
import { VariantDelete } from "../types/VariantDelete";
import {
  VariantImageAssign,
  VariantImageAssignVariables
} from "../types/VariantImageAssign";
import {
  VariantImageUnassign,
  VariantImageUnassignVariables
} from "../types/VariantImageUnassign";
import { VariantUpdate, VariantUpdateVariables } from "../types/VariantUpdate";
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
      VariantUpdate,
      VariantUpdateVariables
    >;
    assignImage: PartialMutationProviderOutput<
      VariantImageAssign,
      VariantImageAssignVariables
    >;
    unassignImage: PartialMutationProviderOutput<
      VariantImageUnassign,
      VariantImageUnassignVariables
    >;
  }>;
  onDelete?: (data: VariantDelete) => void;
  onImageAssign?: (data: VariantImageAssign) => void;
  onImageUnassign?: (data: VariantImageUnassign) => void;
  onUpdate?: (data: VariantUpdate) => void;
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
