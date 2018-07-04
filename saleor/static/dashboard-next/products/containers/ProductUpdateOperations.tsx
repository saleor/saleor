import * as React from "react";
import { Redirect } from "react-router-dom";

import ErrorMessageCard from "../../components/ErrorMessageCard";
import {
  ProductDetailsQuery,
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
        __typename: "ProductImageCountableEdge",
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
  product?: ProductDetailsQuery["product"];
  children: (
    mutations: {
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
                        createProductImage({ variables }),
                      deleteProduct,
                      reorderProductImages: variables => {
                        const imagesMap = {};
                        product.images.edges.forEach(edge => {
                          const image = edge.node;
                          imagesMap[image.id] = image;
                        })
                        const productImages = variables.imagesIds.map((id, index) => ({
                          __typename: "ProductImage",
                          ...imagesMap[id],
                          sortOrder: index,
                        }));
                        const optimisticResponse = {
                          productImageReorder: {
                            __typename: "ProductImageReorder",
                            errors: null,
                            productImages
                          }
                        };
                        reorderProductImages({ variables, optimisticResponse })
                      },
                      updateProduct: variables => updateProduct({ variables })
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
