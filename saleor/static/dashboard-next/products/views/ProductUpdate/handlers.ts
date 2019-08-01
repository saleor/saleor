import { decimal } from "@saleor/misc";
import { ProductUpdatePageSubmitData } from "@saleor/products/components/ProductUpdatePage";
import { ProductDetails_product } from "@saleor/products/types/ProductDetails";
import { ProductImageCreateVariables } from "@saleor/products/types/ProductImageCreate";
import { ProductImageReorderVariables } from "@saleor/products/types/ProductImageReorder";
import { ProductUpdateVariables } from "@saleor/products/types/ProductUpdate";
import { SimpleProductUpdateVariables } from "@saleor/products/types/SimpleProductUpdate";
import { ReorderEvent } from "@saleor/types";
import { arrayMove } from "react-sortable-hoc";

export function createUpdateHandler(
  product: ProductDetails_product,
  updateProduct: (variables: ProductUpdateVariables) => void,
  updateSimpleProduct: (variables: SimpleProductUpdateVariables) => void
) {
  return (data: ProductUpdatePageSubmitData) => {
    const productVariables: ProductUpdateVariables = {
      attributes: data.attributes.map(attribute => ({
        id: attribute.id,
        values: attribute.value[0] === "" ? [] : attribute.value
      })),
      basePrice: decimal(data.basePrice),
      category: data.category,
      chargeTaxes: data.chargeTaxes,
      collections: data.collections,
      descriptionJson: JSON.stringify(data.description),
      id: product.id,
      isPublished: data.isPublished,
      name: data.name,
      publicationDate:
        data.publicationDate !== "" ? data.publicationDate : null,
      seo: {
        description: data.seoDescription,
        title: data.seoTitle
      }
    };

    if (product.productType.hasVariants) {
      updateProduct(productVariables);
    } else {
      updateSimpleProduct({
        ...productVariables,
        productVariantId: product.variants[0].id,
        productVariantInput: {
          quantity: data.stockQuantity,
          sku: data.sku
        }
      });
    }
  };
}

export function createImageUploadHandler(
  id: string,
  createProductImage: (variables: ProductImageCreateVariables) => void
) {
  return (file: File) =>
    createProductImage({
      alt: "",
      image: file,
      product: id
    });
}

export function createImageReorderHandler(
  product: ProductDetails_product,
  reorderProductImages: (variables: ProductImageReorderVariables) => void
) {
  return ({ newIndex, oldIndex }: ReorderEvent) => {
    let ids = product.images.map(image => image.id);
    ids = arrayMove(ids, oldIndex, newIndex);
    reorderProductImages({
      imagesIds: ids,
      productId: product.id
    });
  };
}
