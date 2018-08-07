import * as React from "react";

import {
  ProductDetailsQuery,
  ProductImageReorderMutation,
  ProductImageReorderMutationVariables
} from "../../gql-types";
import { productImagesReorder, TypedProductImagesReorder } from "../mutations";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../..";
import { productDetailsQuery } from "../queries";

interface ProductImagesReorderProviderProps
  extends PartialMutationProviderProps<ProductImageReorderMutation> {
  productId: string;
  productImages: Array<{
    id: string;
    url: string;
  }>;
  children: PartialMutationProviderRenderProps<
    ProductImageReorderMutation,
    ProductImageReorderMutationVariables
  >;
}

const ProductImagesReorderProvider: React.StatelessComponent<
  ProductImagesReorderProviderProps
> = props => (
  <TypedProductImagesReorder
    mutation={productImagesReorder}
    onCompleted={props.onSuccess}
    onError={props.onError}
    update={(cache, { data: { productImageReorder } }) => {
      const data: ProductDetailsQuery = cache.readQuery({
        query: productDetailsQuery,
        variables: { id: props.productId }
      });
      data.product.images.edges.forEach((item, index, array) => {
        array[index].node = productImageReorder.productImages[index];
      });
      cache.writeQuery({ query: productDetailsQuery, data });
    }}
  >
    {(mutate, { data, error, loading }) =>
      props.children({
        data,
        error,
        loading,
        mutate: opts => {
          const productImagesMap = props.productImages.reduce((prev, curr) => {
            prev[curr.id] = curr;
            return prev;
          }, {});
          const productImages = opts.variables.imagesIds.map((id, index) => ({
            __typename: "ProductImage",
            ...productImagesMap[id],
            sortOrder: index
          }));
          const optimisticResponse = {
            productImageReorder: {
              __typename: "ProductImageReorder",
              errors: null,
              productImages
            }
          };
          return mutate({
            optimisticResponse,
            variables: opts.variables
          });
        }
      })
    }
  </TypedProductImagesReorder>
);

export default ProductImagesReorderProvider;
