import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput
} from "../../types";
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
import AttributeCreateProvider from "./AttributeCreate";
import AttributeDeleteProvider from "./AttributeDelete";
import AttributeUpdateProvider from "./AttributeUpdate";
import ProductTypeDeleteProvider from "./ProductTypeDelete";
import ProductTypeUpdateProvider from "./ProductTypeUpdate";

interface ProductTypeOperationsProps extends MutationProviderProps {
  id: string;
  children: MutationProviderRenderProps<{
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
    loading: boolean;
  }>;
  onAttributeCreate: (data: AttributeCreate) => void;
  onAttributeDelete: (data: AttributeDelete) => void;
  onAttributeUpdate: (data: AttributeUpdate) => void;
  onProductTypeDelete: (data: ProductTypeDelete) => void;
  onProductTypeUpdate: (data: ProductTypeUpdate) => void;
}

const ProductTypeOperations: React.StatelessComponent<
  ProductTypeOperationsProps
> = ({
  id,
  children,
  onAttributeCreate,
  onAttributeDelete,
  onAttributeUpdate,
  onError,
  onProductTypeDelete,
  onProductTypeUpdate
}) => {
  return (
    <ProductTypeDeleteProvider
      id={id}
      onError={onError}
      onSuccess={onProductTypeDelete}
    >
      {deleteProductType => (
        <ProductTypeUpdateProvider
          onError={onError}
          onSuccess={onProductTypeUpdate}
        >
          {updateProductType => (
            <AttributeCreateProvider
              onError={onError}
              onSuccess={onAttributeCreate}
            >
              {createAttribute => (
                <AttributeDeleteProvider
                  onError={onError}
                  onSuccess={onAttributeDelete}
                >
                  {deleteAttribute => (
                    <AttributeUpdateProvider
                      onError={onError}
                      onSuccess={onAttributeUpdate}
                    >
                      {updateAttribute =>
                        children({
                          attributeCreate: {
                            data: createAttribute.data,
                            loading: createAttribute.loading,
                            mutate: variables =>
                              createAttribute.mutate({ variables })
                          },
                          deleteAttribute: {
                            data: deleteAttribute.data,
                            loading: deleteAttribute.loading,
                            mutate: variables =>
                              deleteAttribute.mutate({ variables })
                          },
                          deleteProductType: {
                            data: deleteProductType.data,
                            loading: deleteProductType.loading,
                            mutate: () =>
                              deleteProductType.mutate({ variables: { id } })
                          },
                          errors: [],
                          loading: deleteProductType.loading,
                          updateAttribute: {
                            data: updateAttribute.data,
                            loading: updateAttribute.loading,
                            mutate: variables =>
                              updateAttribute.mutate({ variables })
                          },
                          updateProductType: {
                            data: updateProductType.data,
                            loading: updateProductType.loading,
                            mutate: variables =>
                              updateProductType.mutate({ variables })
                          }
                        })
                      }
                    </AttributeUpdateProvider>
                  )}
                </AttributeDeleteProvider>
              )}
            </AttributeCreateProvider>
          )}
        </ProductTypeUpdateProvider>
      )}
    </ProductTypeDeleteProvider>
  );
};
export default ProductTypeOperations;
