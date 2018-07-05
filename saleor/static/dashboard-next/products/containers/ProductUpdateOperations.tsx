import * as React from "react";
import { Redirect } from "react-router-dom";

import { ApolloError } from "apollo-client";
import { MutationProviderChildrenRenderProps } from "../..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import {
  ProductDeleteMutation,
  ProductDeleteMutationVariables,
  ProductDetailsQuery,
  ProductImageCreateMutation,
  ProductImageCreateMutationVariables,
  ProductImageReorderMutationVariables,
  ProductUpdateMutationVariables
} from "../../gql-types";
import { productListUrl } from "../index";
import {
  productDeleteMutation,
  productImageCreateMutation,
  TypedProductDeleteMutation,
  TypedProductImageCreateMutation
} from "../mutations";
import { productDetailsQuery } from "../queries";
import ProductImagesReorderProvider from "./ProductImagesReorder";
import ProductUpdateProvider from "./ProductUpdate";

interface ProductDeleteProviderProps {
  productId: string;
  children: ((
    props: MutationProviderChildrenRenderProps<
      ProductDeleteMutation,
      ProductDeleteMutationVariables
    >
  ) => React.ReactElement<any>);
}

const ProductDeleteProvider: React.StatelessComponent<
  ProductDeleteProviderProps
> = ({ productId, children }) => (
  <TypedProductDeleteMutation
    mutation={productDeleteMutation}
    variables={{ id: productId }}
  >
    {(mutate, { called, error, loading }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      if (called && !loading) {
        return <Redirect to={productListUrl} push={false} />;
      }
      return children({
        called,
        error,
        loading,
        mutate
      });
    }}
  </TypedProductDeleteMutation>
);

interface ProductImageCreateProviderProps {
  productId: string;
  children: ((
    props: MutationProviderChildrenRenderProps<
      ProductImageCreateMutation,
      ProductImageCreateMutationVariables
    >
  ) => React.ReactElement<any>);
}

const ProductImageCreateProvider: React.StatelessComponent<
  ProductImageCreateProviderProps
> = ({ productId, children }) => (
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
  >
    {(mutate, { called, error, loading }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children({
        called,
        error,
        loading,
        mutate
      });
    }}
  </TypedProductImageCreateMutation>
);

interface ProductUpdateOperationsProps {
  product?: ProductDetailsQuery["product"];
  children: (
    props: {
      error: ApolloError;
      loading: boolean;
      createProductImage(variables: ProductImageCreateMutationVariables): void;
      deleteProduct(): void;
      reorderProductImages(
        variables: ProductImageReorderMutationVariables
      ): void;
      updateProduct(variables: ProductUpdateMutationVariables): void;
    }
  ) => React.ReactElement<any>;
}

const ProductUpdateOperations: React.StatelessComponent<
  ProductUpdateOperationsProps
> = ({ product, children }) => {
  const productId = product ? product.id : "";
  return (
    <ProductUpdateProvider productId={productId}>
      {updateProduct => (
        <ProductImagesReorderProvider productId={productId}>
          {reorderProductImages => (
            <ProductImageCreateProvider productId={productId}>
              {createProductImage => (
                <ProductDeleteProvider productId={productId}>
                  {deleteProduct =>
                    children({
                      createProductImage: variables =>
                        createProductImage.mutate({ variables }),
                      deleteProduct: deleteProduct.mutate,
                      error:
                        updateProduct.error ||
                        reorderProductImages.error ||
                        createProductImage.error ||
                        deleteProduct.error,
                      loading:
                        updateProduct.loading ||
                        reorderProductImages.loading ||
                        createProductImage.loading ||
                        deleteProduct.loading,
                      reorderProductImages: variables => {
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
                      },
                      updateProduct: variables =>
                        updateProduct.mutate({ variables })
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
