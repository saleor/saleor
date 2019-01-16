import * as React from "react";

import { getMutationProviderData } from "../../misc";
import { PartialMutationProviderOutput } from "../../types";
import {
  TypedVariantDeleteMutation,
  TypedVariantImageAssignMutation,
  TypedVariantImageUnassignMutation,
  TypedVariantUpdateMutation
} from "../mutations";
import { VariantDelete, VariantDeleteVariables } from "../types/VariantDelete";
import {
  VariantImageAssign,
  VariantImageAssignVariables
} from "../types/VariantImageAssign";
import {
  VariantImageUnassign,
  VariantImageUnassignVariables
} from "../types/VariantImageUnassign";
import { VariantUpdate, VariantUpdateVariables } from "../types/VariantUpdate";

interface VariantDeleteOperationsProps {
  children: (
    props: {
      deleteVariant: PartialMutationProviderOutput<
        VariantDelete,
        VariantDeleteVariables
      >;
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
    }
  ) => React.ReactNode;
  onDelete?: (data: VariantDelete) => void;
  onImageAssign?: (data: VariantImageAssign) => void;
  onImageUnassign?: (data: VariantImageUnassign) => void;
  onUpdate?: (data: VariantUpdate) => void;
}

const VariantUpdateOperations: React.StatelessComponent<
  VariantDeleteOperationsProps
> = ({ children, onDelete, onUpdate, onImageAssign, onImageUnassign }) => {
  return (
    <TypedVariantImageAssignMutation onCompleted={onImageAssign}>
      {(...assignImage) => (
        <TypedVariantImageUnassignMutation onCompleted={onImageUnassign}>
          {(...unassignImage) => (
            <TypedVariantUpdateMutation onCompleted={onUpdate}>
              {(...updateVariant) => (
                <TypedVariantDeleteMutation onCompleted={onDelete}>
                  {(...deleteVariant) =>
                    children({
                      assignImage: getMutationProviderData(...assignImage),
                      deleteVariant: getMutationProviderData(...deleteVariant),
                      unassignImage: getMutationProviderData(...unassignImage),
                      updateVariant: getMutationProviderData(...updateVariant)
                    })
                  }
                </TypedVariantDeleteMutation>
              )}
            </TypedVariantUpdateMutation>
          )}
        </TypedVariantImageUnassignMutation>
      )}
    </TypedVariantImageAssignMutation>
  );
};
export default VariantUpdateOperations;
