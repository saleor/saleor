import { stringify as stringifyQs } from "qs";
import urlJoin from "url-join";

import { BulkAction, Dialog, Pagination, SingleAction } from "../types";

const productTypeSection = "/product-types/";

export const productTypeListPath = productTypeSection;
export type ProductTypeListUrlDialog = "remove";
export type ProductTypeListUrlQueryParams = BulkAction &
  Dialog<ProductTypeListUrlDialog> &
  Pagination;
export const productTypeListUrl = (params?: ProductTypeListUrlQueryParams) =>
  productTypeListPath + "?" + stringifyQs(params);

export const productTypeAddPath = urlJoin(productTypeSection, "add");
export const productTypeAddUrl = productTypeAddPath;

export const productTypePath = (id: string) => urlJoin(productTypeSection, id);
export type ProductTypeUrlDialog =
  | "assign-attribute"
  | "unassign-attribute"
  | "unassign-attributes"
  | "remove";
export type ProductTypeUrlQueryParams = BulkAction &
  Dialog<ProductTypeUrlDialog> &
  SingleAction & {
    type?: string;
  };
export const productTypeUrl = (
  id: string,
  params?: ProductTypeUrlQueryParams
) => productTypePath(encodeURIComponent(id)) + "?" + stringifyQs(params);
