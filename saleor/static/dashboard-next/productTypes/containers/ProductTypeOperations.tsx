import React from "react";

import { getMutationProviderData } from "../../misc";
import { PartialMutationProviderOutput } from "../../types";
import {
  ProductTypeAttributeReorderMutation,
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
  ProductTypeAttributeReorder,
  ProductTypeAttributeReorderVariables
} from "../types/ProductTypeAttributeReorder";
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
    reorderAttribute: PartialMutationProviderOutput<
      ProductTypeAttributeReorder,
      ProductTypeAttributeReorderVariables
    >;
    updateProductType: PartialMutationProviderOutput<
      ProductTypeUpdate,
      ProductTypeUpdateVariables
    >;
  }) => React.ReactNode;
  onAssignAttribute: (data: AssignAttribute) => void;
  onUnassignAttribute: (data: UnassignAttribute) => void;
  onProductTypeAttributeReorder: (data: ProductTypeAttributeReorder) => void;
  onProductTypeDelete: (data: ProductTypeDelete) => void;
  onProductTypeUpdate: (data: ProductTypeUpdate) => void;
}

const ProductTypeOperations: React.StatelessComponent<
  ProductTypeOperationsProps
> = ({
  children,
  onAssignAttribute,
  onUnassignAttribute,
  onProductTypeAttributeReorder,
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
                  {(...unassignAttribute) => (
                    <ProductTypeAttributeReorderMutation
                      onCompleted={onProductTypeAttributeReorder}
                    >
                      {(...reorderAttribute) =>
                        children({
                          assignAttribute: getMutationProviderData(
                            ...assignAttribute
                          ),
                          deleteProductType: getMutationProviderData(
                            ...deleteProductType
                          ),
                          reorderAttribute: getMutationProviderData(
                            ...reorderAttribute
                          ),
                          unassignAttribute: getMutationProviderData(
                            ...unassignAttribute
                          ),
                          updateProductType: getMutationProviderData(
                            ...updateProductType
                          )
                        })
                      }
                    </ProductTypeAttributeReorderMutation>
                  )}
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
