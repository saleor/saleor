import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { Dialog } from "../types";
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
export type ProductUrlDialog = "remove";
export type ProductUrlQueryParams = Dialog<"remove">;
export const productUrl = (id: string, params?: ProductUrlQueryParams) =>
  productPath(encodeURIComponent(id)) + "?" + stringifyQs(params);

export const productVariantEditPath = (productId: string, variantId: string) =>
  urlJoin(productSection, productId, "variant", variantId);
export type ProductVariantEditUrlDialog = "remove";
export type ProductVariantEditUrlQueryParams = Dialog<"remove">;
export const productVariantEditUrl = (
  productId: string,
  variantId: string,
  params?: ProductVariantEditUrlQueryParams
) =>
  productVariantEditPath(
    encodeURIComponent(productId),
    encodeURIComponent(variantId)
  ) +
  "?" +
  stringifyQs(params);

export const productVariantAddPath = (productId: string) =>
  urlJoin(productSection, productId, "variant/add");
export const productVariantAddUrl = (productId: string) =>
  productVariantAddPath(encodeURIComponent(productId));

export const productImagePath = (productId: string, imageId: string) =>
  urlJoin(productSection, productId, "image", imageId);
export type ProductImageUrlDialog = "remove";
export type ProductImageUrlQueryParams = Dialog<"remove">;
export const productImageUrl = (
  productId: string,
  imageId: string,
  params?: ProductImageUrlQueryParams
) =>
  productImagePath(encodeURIComponent(productId), encodeURIComponent(imageId)) +
  "?" +
  stringifyQs(params);
