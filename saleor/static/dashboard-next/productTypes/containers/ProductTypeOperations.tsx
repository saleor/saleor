import * as React from "react";

import { getMutationProviderData } from "../../misc";
import { PartialMutationProviderOutput } from "../../types";
import {
  TypedAttributeCreateMutation,
  TypedAttributeDeleteMutation,
  TypedAttributeUpdateMutation,
  TypedProductTypeDeleteMutation,
  TypedProductTypeUpdateMutation
} from "../mutations";
import {
  AttributeCreate,
  AttributeCreateVariables
} from "../types/AttributeCreate";
import {
  AttributeDelete,
  AttributeDeleteVariables
} from "../types/AttributeDelete";
import {
  AttributeUpdate,
  AttributeUpdateVariables
} from "../types/AttributeUpdate";
import {
  ProductTypeDelete,
  ProductTypeDeleteVariables
} from "../types/ProductTypeDelete";
import {
  ProductTypeUpdate,
  ProductTypeUpdateVariables
} from "../types/ProductTypeUpdate";

interface ProductTypeOperationsProps {
  children: (
    props: {
      attributeCreate: PartialMutationProviderOutput<
        AttributeCreate,
        AttributeCreateVariables
      >;
      deleteAttribute: PartialMutationProviderOutput<
        AttributeDelete,
        AttributeDeleteVariables
      >;
      deleteProductType: PartialMutationProviderOutput<
        ProductTypeDelete,
        ProductTypeDeleteVariables
      >;
      updateAttribute: PartialMutationProviderOutput<
        AttributeUpdate,
        AttributeUpdateVariables
      >;
      updateProductType: PartialMutationProviderOutput<
        ProductTypeUpdate,
        ProductTypeUpdateVariables
      >;
    }
  ) => React.ReactNode;
  onAttributeCreate: (data: AttributeCreate) => void;
  onAttributeDelete: (data: AttributeDelete) => void;
  onAttributeUpdate: (data: AttributeUpdate) => void;
  onProductTypeDelete: (data: ProductTypeDelete) => void;
  onProductTypeUpdate: (data: ProductTypeUpdate) => void;
}

const ProductTypeOperations: React.StatelessComponent<
  ProductTypeOperationsProps
> = ({
  children,
  onAttributeCreate,
  onAttributeDelete,
  onAttributeUpdate,
  onProductTypeDelete,
  onProductTypeUpdate
}) => {
  return (
    <TypedProductTypeDeleteMutation onCompleted={onProductTypeDelete}>
      {(...deleteProductType) => (
        <TypedProductTypeUpdateMutation onCompleted={onProductTypeUpdate}>
          {(...updateProductType) => (
            <TypedAttributeCreateMutation onCompleted={onAttributeCreate}>
              {(...createAttribute) => (
                <TypedAttributeDeleteMutation onCompleted={onAttributeDelete}>
                  {(...deleteAttribute) => (
                    <TypedAttributeUpdateMutation
                      onCompleted={onAttributeUpdate}
                    >
                      {(...updateAttribute) =>
                        children({
                          attributeCreate: getMutationProviderData(
                            ...createAttribute
                          ),
                          deleteAttribute: getMutationProviderData(
                            ...deleteAttribute
                          ),
                          deleteProductType: getMutationProviderData(
                            ...deleteProductType
                          ),
                          updateAttribute: getMutationProviderData(
                            ...updateAttribute
                          ),
                          updateProductType: getMutationProviderData(
                            ...updateProductType
                          )
                        })
                      }
                    </TypedAttributeUpdateMutation>
                  )}
                </TypedAttributeDeleteMutation>
              )}
            </TypedAttributeCreateMutation>
          )}
        </TypedProductTypeUpdateMutation>
      )}
    </TypedProductTypeDeleteMutation>
  );
};
export default ProductTypeOperations;
