import * as React from "react";

import { TypedProductImagesReorder } from "../mutations";
import {
  ProductImageReorder,
  ProductImageReorderVariables
} from "../types/ProductImageReorder";

import {
  PartialMutationProviderProps,
  PartialMutationProviderRenderProps
} from "../../types";

interface ProductImagesReorderProviderProps
  extends PartialMutationProviderProps<ProductImageReorder> {
  productId: string;
  productImages: Array<{
    id: string;
    url: string;
  }>;
  children: PartialMutationProviderRenderProps<
    ProductImageReorder,
    ProductImageReorderVariables
  >;
}

const ProductImagesReorderProvider: React.StatelessComponent<
  ProductImagesReorderProviderProps
> = props => (
  <TypedProductImagesReorder
    onCompleted={props.onSuccess}
    onError={props.onError}
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
              product: {
                __typename: "Product",
                id: props.productId,
                images: productImages
              }
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
