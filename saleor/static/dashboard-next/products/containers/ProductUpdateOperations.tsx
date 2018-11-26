import * as React from "react";

import { maybe } from "../../misc";
import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput,
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";
import {
  TypedProductDeleteMutation,
  TypedProductImageCreateMutation,
  TypedProductImageDeleteMutation
} from "../mutations";
import { ProductDelete, ProductDeleteVariables } from "../types/ProductDelete";
import { ProductDetails_product } from "../types/ProductDetails";
import {
  ProductImageCreate,
  ProductImageCreateVariables
} from "../types/ProductImageCreate";
import {
  ProductImageDelete,
  ProductImageDeleteVariables
} from "../types/ProductImageDelete";
import {
  ProductImageReorder,
  ProductImageReorderVariables
} from "../types/ProductImageReorder";
import { ProductUpdate, ProductUpdateVariables } from "../types/ProductUpdate";
import ProductImagesReorderProvider from "./ProductImagesReorder";
import ProductUpdateProvider from "./ProductUpdate";

interface ProductDeleteProviderProps
  extends PartialMutationProviderProps<ProductDelete> {
  productId: string;
  children: PartialMutationProviderRenderProps<
    ProductDelete,
    ProductDeleteVariables
  >;
}

const ProductDeleteProvider: React.StatelessComponent<
  ProductDeleteProviderProps
> = ({ productId, children, onError, onSuccess }) => (
  <TypedProductDeleteMutation
    variables={{ id: productId }}
    onCompleted={onSuccess}
    onError={onError}
  >
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedProductDeleteMutation>
);

interface ProductImageCreateProviderProps
  extends PartialMutationProviderProps<ProductImageCreate> {
  children: PartialMutationProviderRenderProps<
    ProductImageCreate,
    ProductImageCreateVariables
  >;
}

const ProductImageCreateProvider: React.StatelessComponent<
  ProductImageCreateProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedProductImageCreateMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedProductImageCreateMutation>
);

interface ProductImageDeleteProviderProps
  extends PartialMutationProviderProps<ProductImageDelete> {
  children: PartialMutationProviderRenderProps<
    ProductImageDelete,
    ProductImageDeleteVariables
  >;
}

const ProductImageDeleteProvider: React.StatelessComponent<
  ProductImageDeleteProviderProps
> = ({ children, onError, onSuccess }) => (
  <TypedProductImageDeleteMutation onCompleted={onSuccess} onError={onError}>
    {(mutate, { data, error, loading }) =>
      children({
        data,
        error,
        loading,
        mutate
      })
    }
  </TypedProductImageDeleteMutation>
);

interface ProductUpdateOperationsProps extends MutationProviderProps {
  product?: ProductDetails_product;
  children: MutationProviderRenderProps<{
    createProductImage: PartialMutationProviderOutput<
      ProductImageCreate,
      ProductImageCreateVariables
    >;
    deleteProduct: PartialMutationProviderOutput;
    deleteProductImage: PartialMutationProviderOutput<
      ProductImageDelete,
      ProductImageDeleteVariables
    >;
    reorderProductImages: PartialMutationProviderOutput<
      ProductImageReorder,
      ProductImageReorderVariables
    >;
    updateProduct: PartialMutationProviderOutput<
      ProductUpdate,
      ProductUpdateVariables
    >;
  }>;
  onDelete?: (data: ProductDelete) => void;
  onImageCreate?: (data: ProductImageCreate) => void;
  onImageDelete?: (data: ProductImageDelete) => void;
  onImageReorder?: (data: ProductImageReorder) => void;
  onUpdate?: (data: ProductUpdate) => void;
}

const ProductUpdateOperations: React.StatelessComponent<
  ProductUpdateOperationsProps
> = ({
  product,
  children,
  onDelete,
  onError,
  onImageDelete,
  onImageCreate,
  onImageReorder,
  onUpdate
}) => {
  const productId = product ? product.id : "";
  return (
    <ProductUpdateProvider onError={onError} onSuccess={onUpdate}>
      {updateProduct => (
        <ProductImagesReorderProvider
          productId={productId}
          productImages={maybe(() => product.images, [])}
          onError={onError}
          onSuccess={onImageReorder}
        >
          {reorderProductImages => (
            <ProductImageCreateProvider
              onError={onError}
              onSuccess={onImageCreate}
            >
              {createProductImage => (
                <ProductDeleteProvider
                  productId={productId}
                  onError={onError}
                  onSuccess={onDelete}
                >
                  {deleteProduct => (
                    <ProductImageDeleteProvider
                      onError={onError}
                      onSuccess={onImageDelete}
                    >
                      {deleteProductImage =>
                        children({
                          createProductImage: {
                            data: createProductImage.data,
                            loading: createProductImage.loading,
                            mutate: variables =>
                              createProductImage.mutate({ variables })
                          },
                          deleteProduct: {
                            data: deleteProduct.data,
                            loading: deleteProduct.loading,
                            mutate: deleteProduct.mutate
                          },
                          deleteProductImage: {
                            data: deleteProductImage.data,
                            loading: deleteProductImage.loading,
                            mutate: variables =>
                              deleteProductImage.mutate({ variables })
                          },
                          errors:
                            updateProduct &&
                            updateProduct.data &&
                            updateProduct.data.productUpdate
                              ? updateProduct.data.productUpdate.errors
                              : [],
                          reorderProductImages: {
                            data: reorderProductImages.data,
                            loading: reorderProductImages.loading,
                            mutate: variables =>
                              reorderProductImages.mutate({ variables })
                          },
                          updateProduct: {
                            called: updateProduct.called,
                            data: updateProduct.data,
                            loading: updateProduct.loading,
                            mutate: variables =>
                              updateProduct.mutate({ variables })
                          }
                        })
                      }
                    </ProductImageDeleteProvider>
                  )}
                </ProductDeleteProvider>
              )}
            </ProductImageCreateProvider>
          )}
        </ProductImagesReorderProvider>
      )}
    </ProductUpdateProvider>
  );
};
export default ProductUpdateOperations;
