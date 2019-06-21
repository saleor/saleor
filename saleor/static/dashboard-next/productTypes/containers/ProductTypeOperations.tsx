import React from "react";

import { getMutationProviderData } from "../../misc";
import { PartialMutationProviderOutput } from "../../types";
import {
  TypedAssignAttributeMutation,
  TypedProductTypeDeleteMutation,
  TypedProductTypeUpdateMutation,
  TypedUnassignAttributeMutation
} from "../mutations";
import {
  AssignAttribute,
  AssignAttributeVariables
} from "../types/AssignAttribute";
import {
  ProductTypeDelete,
  ProductTypeDeleteVariables
} from "../types/ProductTypeDelete";
import {
  ProductTypeUpdate,
  ProductTypeUpdateVariables
} from "../types/ProductTypeUpdate";
import {
  UnassignAttribute,
  UnassignAttributeVariables
} from "../types/UnassignAttribute";

interface ProductTypeOperationsProps {
  children: (props: {
    assignAttribute: PartialMutationProviderOutput<
      AssignAttribute,
      AssignAttributeVariables
    >;
    unassignAttribute: PartialMutationProviderOutput<
      UnassignAttribute,
      UnassignAttributeVariables
    >;
    deleteProductType: PartialMutationProviderOutput<
      ProductTypeDelete,
      ProductTypeDeleteVariables
    >;
    updateProductType: PartialMutationProviderOutput<
      ProductTypeUpdate,
      ProductTypeUpdateVariables
    >;
  }) => React.ReactNode;
  onAssignAttribute: (data: AssignAttribute) => void;
  onUnassignAttribute: (data: UnassignAttribute) => void;
  onProductTypeDelete: (data: ProductTypeDelete) => void;
  onProductTypeUpdate: (data: ProductTypeUpdate) => void;
}

const ProductTypeOperations: React.StatelessComponent<
  ProductTypeOperationsProps
> = ({
  children,
  onAssignAttribute,
  onUnassignAttribute,
  onProductTypeDelete,
  onProductTypeUpdate
}) => {
  return (
    <TypedProductTypeDeleteMutation onCompleted={onProductTypeDelete}>
      {(...deleteProductType) => (
        <TypedProductTypeUpdateMutation onCompleted={onProductTypeUpdate}>
          {(...updateProductType) => (
            <TypedAssignAttributeMutation onCompleted={onAssignAttribute}>
              {(...assignAttribute) => (
                <TypedUnassignAttributeMutation
                  onCompleted={onUnassignAttribute}
                >
                  {(...unassignAttribute) =>
                    children({
                      assignAttribute: getMutationProviderData(
                        ...assignAttribute
                      ),
                      deleteProductType: getMutationProviderData(
                        ...deleteProductType
                      ),
                      unassignAttribute: getMutationProviderData(
                        ...unassignAttribute
                      ),
                      updateProductType: getMutationProviderData(
                        ...updateProductType
                      )
                    })
                  }
                </TypedUnassignAttributeMutation>
              )}
            </TypedAssignAttributeMutation>
          )}
        </TypedProductTypeUpdateMutation>
      )}
    </TypedProductTypeDeleteMutation>
  );
};
export default ProductTypeOperations;
