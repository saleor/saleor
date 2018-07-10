import * as React from "react";

import {
  MutationProviderPartialOutput,
  MutationProviderProps,
  MutationProviderRenderProps
} from "../..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
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
  extends MutationProviderProps<ProductDeleteMutation> {
  productId: string;
  children: ((
    props: MutationProviderRenderProps<
      ProductDeleteMutation,
      ProductDeleteMutationVariables
    >
  ) => React.ReactElement<any>);
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
    {(mutate, { data, error, loading }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedProductDeleteMutation>
);

interface ProductImageCreateProviderProps
  extends MutationProviderProps<ProductImageCreateMutation> {
  productId: string;
  children: ((
    props: MutationProviderRenderProps<
      ProductImageCreateMutation,
      ProductImageCreateMutationVariables
    >
  ) => React.ReactElement<any>);
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
    {(mutate, { data, error, loading }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children({
        data,
        error,
        loading,
        mutate
      });
    }}
  </TypedProductImageCreateMutation>
);

interface ProductUpdateOperationsProps
  extends MutationProviderProps<ProductImageCreateMutation> {
  product?: ProductDetailsQuery["product"];
  children: (
    props: {
      createProductImage: MutationProviderPartialOutput<
        ProductImageCreateMutation,
        ProductImageCreateMutationVariables
      >;
      deleteProduct: MutationProviderPartialOutput;
      reorderProductImages: Exclude<
        MutationProviderPartialOutput<
          ProductImageReorderMutation,
          ProductImageReorderMutationVariables
        >,
        { error: any }
      >;
      updateProduct: MutationProviderPartialOutput<
        ProductUpdateMutation,
        ProductUpdateMutationVariables
      >;
    }
  ) => React.ReactElement<any>;
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
  onImageCreate,
  onImageReorder,
  onUpdate
}) => {
  const productId = product ? product.id : "";
  return (
    <ProductUpdateProvider productId={productId} onSuccess={onUpdate}>
      {updateProduct => (
        <ProductImagesReorderProvider
          productId={productId}
          onSuccess={onImageReorder}
        >
          {reorderProductImages => (
            <ProductImageCreateProvider
              productId={productId}
              onSuccess={onImageCreate}
            >
              {createProductImage => (
                <ProductDeleteProvider
                  productId={productId}
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
