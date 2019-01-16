import * as React from "react";

import { TypedMutationInnerProps } from "../../mutations";
import { TypedProductImagesReorder } from "../mutations";
import {
  ProductImageReorder,
  ProductImageReorderVariables
} from "../types/ProductImageReorder";

interface ProductImagesReorderProviderProps
  extends TypedMutationInnerProps<
    ProductImageReorder,
    ProductImageReorderVariables
  > {
  productId: string;
  productImages: Array<{
    id: string;
    url: string;
  }>;
}

const ProductImagesReorderProvider: React.StatelessComponent<
  ProductImagesReorderProviderProps
> = ({ children, productId, productImages, ...mutationProps }) => (
  <TypedProductImagesReorder {...mutationProps}>
    {(mutate, mutationResult) =>
      children(opts => {
        const productImagesMap = productImages.reduce((prev, curr) => {
          prev[curr.id] = curr;
          return prev;
        }, {});
        const newProductImages = opts.variables.imagesIds.map((id, index) => ({
          __typename: "ProductImage",
          ...productImagesMap[id],
          sortOrder: index
        }));
        const optimisticResponse: typeof mutationResult["data"] = {
          productImageReorder: {
            __typename: "ProductImageReorder",
            errors: null,
            product: {
              __typename: "Product",
              id: productId,
              images: newProductImages
            }
          }
        };
        return mutate({
          ...opts,
          optimisticResponse
        });
      }, mutationResult)
    }
  </TypedProductImagesReorder>
);

export default ProductImagesReorderProvider;
