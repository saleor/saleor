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
  productDeleteMutation,
  productImageCreateMutation,
  productImageDeleteMutation,
  TypedProductDeleteMutation,
  TypedProductImageCreateMutation,
  TypedProductImageDeleteMutation
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

interface ProductImageDeleteProviderProps
  extends PartialMutationProviderProps<ProductImageDeleteMutation> {
  children: PartialMutationProviderRenderProps<
    ProductImageDeleteMutation,
    ProductImageDeleteMutationVariables
  >;
  productId: string;
}

const ProductImageDeleteProvider: React.StatelessComponent<
  ProductImageDeleteProviderProps
> = ({ children, productId, onError, onSuccess }) => (
  <TypedProductImageDeleteMutation
    mutation={productImageDeleteMutation}
    onCompleted={onSuccess}
    onError={onError}
    update={(cache, { data: { productImageDelete } }) => {
      const data: ProductDetailsQuery = cache.readQuery({
        query: productDetailsQuery,
        variables: { id: productId }
      });
      data.product.images.edges = data.product.images.edges.filter(
        edge => edge.node.id !== productImageDelete.productImage.id
      );
      cache.writeQuery({ query: productDetailsQuery, data });
    }}
  >
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
                  {deleteProduct => (
                    <ProductImageDeleteProvider
                      productId={productId}
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
                            mutate: variables => {
                              const optimisticResponse = {
                                productImageDelete: {
                                  __typename: "ProductImageDelete",
                                  productImage: {
                                    __typename: "ProductImage",
                                    id: variables.id
                                  }
                                }
                              };
                              deleteProductImage.mutate({
                                optimisticResponse,
                                variables
                              });
                            }
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
