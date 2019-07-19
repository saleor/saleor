import React from "react";
import { MutationFn } from "react-apollo";

import {
  AttributeReorderInput,
  AttributeTypeEnum
} from "@saleor/types/globalTypes";
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
  ProductTypeDetailsFragment,
  ProductTypeDetailsFragment_productAttributes
} from "../types/ProductTypeDetailsFragment";
import {
  ProductTypeUpdate,
  ProductTypeUpdateVariables
} from "../types/ProductTypeUpdate";
import {
  UnassignAttribute,
  UnassignAttributeVariables
} from "../types/UnassignAttribute";

function moveAttribute(
  attributes:
    | ProductTypeDetailsFragment_productAttributes[]
    | ProductTypeDetailsFragment_productAttributes[],
  move: AttributeReorderInput
) {
  const attributeIndex = attributes.findIndex(
    attribute => attribute.id === move.id
  );
  const newIndex = attributeIndex + move.sortOrder;

  const attributesWithoutMovedOne = [
    ...attributes.slice(0, attributeIndex),
    ...attributes.slice(attributeIndex + 1)
  ];

  return [
    ...attributesWithoutMovedOne.slice(0, newIndex),
    attributes[attributeIndex],
    ...attributesWithoutMovedOne.slice(newIndex)
  ];
}

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
  productType: ProductTypeDetailsFragment;
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
  productType,
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
                      {(
                        reorderAttributeMutation,
                        reorderAttributeMutationResult
                      ) => {
                        const reorderAttributeMutationFn: MutationFn<
                          ProductTypeAttributeReorder,
                          ProductTypeAttributeReorderVariables
                        > = opts => {
                          const optimisticResponse: ProductTypeAttributeReorder = {
                            productTypeReorderAttributes: {
                              __typename: "ProductTypeReorderAttributes" as "ProductTypeReorderAttributes",
                              errors: [],
                              productType: {
                                ...productType,
                                productAttributes:
                                  opts.variables.type ===
                                  AttributeTypeEnum.PRODUCT
                                    ? moveAttribute(
                                        productType.productAttributes,
                                        opts.variables.move
                                      )
                                    : productType.productAttributes,
                                variantAttributes:
                                  opts.variables.type ===
                                  AttributeTypeEnum.VARIANT
                                    ? moveAttribute(
                                        productType.variantAttributes,
                                        opts.variables.move
                                      )
                                    : productType.variantAttributes
                              }
                            }
                          };
                          return reorderAttributeMutation({
                            ...opts,
                            optimisticResponse
                          });
                        };

                        return children({
                          assignAttribute: getMutationProviderData(
                            ...assignAttribute
                          ),
                          deleteProductType: getMutationProviderData(
                            ...deleteProductType
                          ),
                          reorderAttribute: getMutationProviderData(
                            reorderAttributeMutationFn,
                            reorderAttributeMutationResult
                          ),
                          unassignAttribute: getMutationProviderData(
                            ...unassignAttribute
                          ),
                          updateProductType: getMutationProviderData(
                            ...updateProductType
                          )
                        });
                      }}
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
