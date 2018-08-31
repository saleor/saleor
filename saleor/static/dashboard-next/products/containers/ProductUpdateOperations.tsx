import * as React from "react";

import {
  MutationProviderProps,
  MutationProviderRenderProps,
  PartialMutationProviderOutput,
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import {
  ProductDeleteMutation,
  ProductDeleteMutationVariables,
  ProductDetailsQuery,
  ProductImageCreateMutation,
  ProductImageCreateMutationVariables,
  ProductImageDeleteMutation,
  ProductImageDeleteMutationVariables,
  ProductImageReorderMutation,
  ProductImageReorderMutationVariables,
  ProductUpdateMutation,
  ProductUpdateMutationVariables
} from "../../gql-types";
import {
  TypedProductDeleteMutation,
  TypedProductImageCreateMutation,
  TypedProductImageDeleteMutation
} from "../mutations";
import ProductImagesReorderProvider from "./ProductImagesReorder";
import ProductUpdateProvider from "./ProductUpdate";

interface ProductDeleteProviderProps
  extends PartialMutationProviderProps<ProductDeleteMutation> {
  productId: string;
  children: PartialMutationProviderRenderProps<
    ProductDeleteMutation,
    ProductDeleteMutationVariables
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
  extends PartialMutationProviderProps<ProductImageCreateMutation> {
  children: PartialMutationProviderRenderProps<
    ProductImageCreateMutation,
    ProductImageCreateMutationVariables
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
  extends PartialMutationProviderProps<ProductImageDeleteMutation> {
  children: PartialMutationProviderRenderProps<
    ProductImageDeleteMutation,
    ProductImageDeleteMutationVariables
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
  product?: ProductDetailsQuery["product"];
  children: MutationProviderRenderProps<{
    createProductImage: PartialMutationProviderOutput<
      ProductImageCreateMutation,
      ProductImageCreateMutationVariables
    >;
    deleteProduct: PartialMutationProviderOutput;
    deleteProductImage: PartialMutationProviderOutput<
      ProductImageDeleteMutation,
      ProductImageDeleteMutationVariables
    >;
    reorderProductImages: PartialMutationProviderOutput<
      ProductImageReorderMutation,
      ProductImageReorderMutationVariables
    >;
    updateProduct: PartialMutationProviderOutput<
      ProductUpdateMutation,
      ProductUpdateMutationVariables
    >;
  }>;
  onDelete?: (data: ProductDeleteMutation) => void;
  onImageCreate?: (data: ProductImageCreateMutation) => void;
  onImageDelete?: (data: ProductImageDeleteMutation) => void;
  onImageReorder?: (data: ProductImageReorderMutation) => void;
  onUpdate?: (data: ProductUpdateMutation) => void;
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
          productImages={
            product && product.images && product.images.edges
              ? product.images.edges.map(edge => edge.node)
              : []
          }
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
