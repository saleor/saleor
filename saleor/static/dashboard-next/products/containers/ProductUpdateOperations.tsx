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
  ProductImageReorderMutation,
  ProductImageReorderMutationVariables,
  ProductUpdateMutation,
  ProductUpdateMutationVariables
} from "../../gql-types";
import {
  productDeleteMutation,
  productImageCreateMutation,
  TypedProductDeleteMutation,
  TypedProductImageCreateMutation
} from "../mutations";
import { productDetailsQuery } from "../queries";
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
    mutation={productDeleteMutation}
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
  productId: string;
  children: PartialMutationProviderRenderProps<
    ProductImageCreateMutation,
    ProductImageCreateMutationVariables
  >;
}

const ProductImageCreateProvider: React.StatelessComponent<
  ProductImageCreateProviderProps
> = ({ productId, children, onError, onSuccess }) => (
  <TypedProductImageCreateMutation
    mutation={productImageCreateMutation}
    update={(cache, { data: { productImageCreate } }) => {
      const data: ProductDetailsQuery = cache.readQuery({
        query: productDetailsQuery,
        variables: { id: productId }
      });
      const edge = {
        __typename: "ProductImageCountableEdge",
        node: productImageCreate.productImage
      };
      data.product.images.edges.push(edge);
      cache.writeQuery({ query: productDetailsQuery, data });
    }}
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
  </TypedProductImageCreateMutation>
);

interface ProductUpdateOperationsProps extends MutationProviderProps {
  product?: ProductDetailsQuery["product"];
  children: MutationProviderRenderProps<{
    createProductImage: PartialMutationProviderOutput<
      ProductImageCreateMutation,
      ProductImageCreateMutationVariables
    >;
    deleteProduct: PartialMutationProviderOutput;
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
  onImageCreate,
  onImageReorder,
  onUpdate
}) => {
  const productId = product ? product.id : "";
  return (
    <ProductUpdateProvider
      productId={productId}
      onError={onError}
      onSuccess={onUpdate}
    >
      {updateProduct => (
        <ProductImagesReorderProvider
          productId={productId}
          onError={onError}
          onSuccess={onImageReorder}
        >
          {reorderProductImages => (
            <ProductImageCreateProvider
              productId={productId}
              onError={onError}
              onSuccess={onImageCreate}
            >
              {createProductImage => (
                <ProductDeleteProvider
                  productId={productId}
                  onError={onError}
                  onSuccess={onDelete}
                >
                  {deleteProduct =>
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
                      errors:
                        updateProduct &&
                        updateProduct.data &&
                        updateProduct.data.productUpdate
                          ? updateProduct.data.productUpdate.errors
                          : [],
                      reorderProductImages: {
                        data: reorderProductImages.data,
                        loading: reorderProductImages.loading,
                        mutate: variables => {
                          const imagesMap = {};
                          product.images.edges.forEach(edge => {
                            const image = edge.node;
                            imagesMap[image.id] = image;
                          });
                          const productImages = variables.imagesIds.map(
                            (id, index) => ({
                              __typename: "ProductImage",
                              ...imagesMap[id],
                              sortOrder: index
                            })
                          );
                          const optimisticResponse = {
                            productImageReorder: {
                              __typename: "ProductImageReorder",
                              errors: null,
                              productImages
                            }
                          };
                          reorderProductImages.mutate({
                            optimisticResponse,
                            variables
                          });
                        }
                      },
                      updateProduct: {
                        data: updateProduct.data,
                        loading: updateProduct.loading,
                        mutate: variables => updateProduct.mutate({ variables })
                      }
                    })
                  }
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
