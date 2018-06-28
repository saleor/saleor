import * as React from "react";
import { Redirect } from "react-router-dom";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import {
  ProductDetailsQuery,
  ProductImageCreateMutationVariables,
  ProductImageReorderMutationVariables
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

interface ProductDeleteProviderProps {
  productId: string;
  children: ((deleteProduct: () => void) => React.ReactElement<any>);
}

const ProductDeleteProvider: React.StatelessComponent<
  ProductDeleteProviderProps
> = ({ productId, children }) => (
  <TypedProductDeleteMutation
    mutation={productDeleteMutation}
    variables={{ id: productId }}
  >
    {(deleteProduct, { called, loading, error }) => {
      if (called && !loading) {
        return <Redirect to={productListUrl} push={false} />;
      }
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children(() => deleteProduct());
    }}
  </TypedProductDeleteMutation>
);

interface ProductImageCreateProviderProps {
  productId: string;
  children: any;
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
        __typename: "ProductImageCountableEdge", // FIXME: check if this has to be hardcoded
        node: productImageCreate.productImage
      };
      data.product.images.edges.push(edge);
      cache.writeQuery({ query: productDetailsQuery, data });
    }}
  >
    {(createProductImage, { error }) => {
      if (error) {
        return <ErrorMessageCard message={error.message} />;
      }
      return children(createProductImage);
    }}
  </TypedProductImageCreateMutation>
);

interface ProductUpdateOperationsProps {
  productId: string;
  children: (
    mutations: {
      createProductImage(variables: ProductImageCreateMutationVariables): void;
      deleteProduct(): void;
      reorderProductImages(
        variables: ProductImageReorderMutationVariables
      ): void;
    }
  ) => React.ReactElement<any>;
}

const ProductUpdateOperations: React.StatelessComponent<
  ProductUpdateOperationsProps
> = ({ productId, children }) => {
  return (
    <ProductImagesReorderProvider productId={productId}>
      {reorderProductImages => (
        <ProductImageCreateProvider productId={productId}>
          {createProductImage => (
            <ProductDeleteProvider productId={productId}>
              {deleteProduct =>
                children({
                  createProductImage: variables =>
                    createProductImage({ variables }),
                  deleteProduct,
                  reorderProductImages: variables =>
                    reorderProductImages({ variables })
                })
              }
            </ProductDeleteProvider>
          )}
        </ProductImageCreateProvider>
      )}
    </ProductImagesReorderProvider>
  );
};
export default ProductUpdateOperations;
