import * as React from "react";

import { getMutationProviderData, maybe } from "../../misc";
import { PartialMutationProviderOutput } from "../../types";
import {
  TypedProductDeleteMutation,
  TypedProductImageCreateMutation,
  TypedProductImageDeleteMutation,
  TypedProductUpdateMutation
} from "../mutations";
import { ProductDelete, ProductDeleteVariables } from "../types/ProductDelete";
import { ProductDetails_product } from "../types/ProductDetails";
import {
  ProductImageCreate,
  ProductImageCreateVariables
} from "../types/ProductImageCreate";
import {
  ProductImageDelete,
  ProductImageDeleteVariables
} from "../types/ProductImageDelete";
import {
  ProductImageReorder,
  ProductImageReorderVariables
} from "../types/ProductImageReorder";
import { ProductUpdate, ProductUpdateVariables } from "../types/ProductUpdate";
import ProductImagesReorderProvider from "./ProductImagesReorder";

interface ProductUpdateOperationsProps {
  product: ProductDetails_product;
  children: (
    props: {
      createProductImage: PartialMutationProviderOutput<
        ProductImageCreate,
        ProductImageCreateVariables
      >;
      deleteProduct: PartialMutationProviderOutput<
        ProductDelete,
        ProductDeleteVariables
      >;
      deleteProductImage: PartialMutationProviderOutput<
        ProductImageDelete,
        ProductImageDeleteVariables
      >;
      reorderProductImages: PartialMutationProviderOutput<
        ProductImageReorder,
        ProductImageReorderVariables
      >;
      updateProduct: PartialMutationProviderOutput<
        ProductUpdate,
        ProductUpdateVariables
      >;
    }
  ) => React.ReactNode;
  onDelete?: (data: ProductDelete) => void;
  onImageCreate?: (data: ProductImageCreate) => void;
  onImageDelete?: (data: ProductImageDelete) => void;
  onImageReorder?: (data: ProductImageReorder) => void;
  onUpdate?: (data: ProductUpdate) => void;
}

const ProductUpdateOperations: React.StatelessComponent<
  ProductUpdateOperationsProps
> = ({
  product,
  children,
  onDelete,
  onImageDelete,
  onImageCreate,
  onImageReorder,
  onUpdate
}) => {
  const productId = product ? product.id : "";
  return (
    <TypedProductUpdateMutation onCompleted={onUpdate}>
      {(...updateProduct) => (
        <ProductImagesReorderProvider
          productId={productId}
          productImages={maybe(() => product.images, [])}
          onCompleted={onImageReorder}
        >
          {(...reorderProductImages) => (
            <TypedProductImageCreateMutation onCompleted={onImageCreate}>
              {(...createProductImage) => (
                <TypedProductDeleteMutation onCompleted={onDelete}>
                  {(...deleteProduct) => (
                    <TypedProductImageDeleteMutation
                      onCompleted={onImageDelete}
                    >
                      {(...deleteProductImage) =>
                        children({
                          createProductImage: getMutationProviderData(
                            ...createProductImage
                          ),
                          deleteProduct: getMutationProviderData(
                            ...deleteProduct
                          ),
                          deleteProductImage: getMutationProviderData(
                            ...deleteProductImage
                          ),
                          reorderProductImages: getMutationProviderData(
                            ...reorderProductImages
                          ),
                          updateProduct: getMutationProviderData(
                            ...updateProduct
                          )
                        })
                      }
                    </TypedProductImageDeleteMutation>
                  )}
                </TypedProductDeleteMutation>
              )}
            </TypedProductImageCreateMutation>
          )}
        </ProductImagesReorderProvider>
      )}
    </TypedProductUpdateMutation>
  );
};
export default ProductUpdateOperations;
