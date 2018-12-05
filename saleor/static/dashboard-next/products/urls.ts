import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";
import { ProductListQueryParams } from "./views/ProductList";

const productSection = "/products/";

export const productAddPath = urlJoin(productSection, "add");
export const productAddUrl = productAddPath;

export const productListPath = productSection;
export const productListUrl = (params?: ProductListQueryParams): string => {
  if (params === undefined) {
    return productListPath;
  } else {
    return urlJoin(productListPath, "?" + stringifyQs(params));
  }
};

export const productPath = (id: string) => urlJoin(productSection, id);
export const productUrl = (id: string) => productPath(encodeURIComponent(id));

export const productVariantEditPath = (productId: string, variantId: string) =>
  urlJoin(productSection, productId, "variant", variantId);
export const productVariantEditUrl = (productId: string, variantId: string) =>
  productVariantEditPath(
    encodeURIComponent(productId),
    encodeURIComponent(variantId)
  );

export const productVariantAddPath = (productId: string) =>
  urlJoin(productSection, productId, "variant/add");
export const productVariantAddUrl = (productId: string) =>
  productVariantAddPath(encodeURIComponent(productId));

export const productImagePath = (productId: string, imageId: string) =>
  urlJoin(productSection, productId, "image", imageId);
export const productImageUrl = (productId: string, imageId: string) =>
  productImagePath(encodeURIComponent(productId), encodeURIComponent(imageId));
