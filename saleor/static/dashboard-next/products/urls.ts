import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";
import { ProductListQueryParams } from "./views/ProductList";

const productSection = "/products/";
export const productAddUrl = urlJoin(productSection, "add");
export const productListUrl = (params?: ProductListQueryParams): string => {
  const productList = productSection;
  if (params === undefined) {
    return productList;
  } else {
    return urlJoin(productList, "?" + stringifyQs(params));
  }
};
export const productUrl = (id: string) => urlJoin(productSection, id);
export const productVariantEditUrl = (productId: string, variantId: string) =>
  urlJoin(productSection, productId, "variant", variantId);

export const productVariantAddUrl = (productId: string) =>
  urlJoin(productSection, productId, "variant/add");

export const productImageUrl = (productId: string, imageId: string) =>
  urlJoin(productSection, productId, "image", imageId);
