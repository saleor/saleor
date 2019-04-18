import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { ActiveTab, BulkAction, Dialog, Pagination } from "../types";
import { SaleDetailsPageTab } from "./components/SaleDetailsPage";
import { VoucherDetailsPageTab } from "./components/VoucherDetailsPage";

export const discountSection = "/discounts/";

export const saleSection = urlJoin(discountSection, "sales");
export const saleListPath = saleSection;
export type SaleListUrlDialog = "remove";
export type SaleListUrlQueryParams = BulkAction &
  Dialog<SaleListUrlDialog> &
  Pagination;
export const saleListUrl = (params?: SaleListUrlQueryParams) =>
  saleListPath + "?" + stringifyQs(params);
export const salePath = (id: string) => urlJoin(saleSection, id);
export type SaleUrlDialog =
  | "assign-category"
  | "assign-collection"
  | "assign-product"
  | "unassign-category"
  | "unassign-collection"
  | "unassign-product"
  | "remove";
export type SaleUrlQueryParams = Pagination &
  BulkAction &
  Dialog<SaleUrlDialog> &
  ActiveTab<SaleDetailsPageTab>;
export const saleUrl = (id: string, params?: SaleUrlQueryParams) =>
  salePath(encodeURIComponent(id)) + "?" + stringifyQs(params);
export const saleAddPath = urlJoin(saleSection, "add");
export const saleAddUrl = saleAddPath;

export const voucherSection = urlJoin(discountSection, "vouchers");
export const voucherListPath = voucherSection;
export type VoucherListUrlDialog = "remove";
export type VoucherListUrlQueryParams = BulkAction &
  Dialog<VoucherListUrlDialog> &
  Pagination;
export const voucherListUrl = (params?: VoucherListUrlQueryParams) =>
  voucherListPath + "?" + stringifyQs(params);
export const voucherPath = (id: string) => urlJoin(voucherSection, id);
export type VoucherUrlDialog =
  | "assign-category"
  | "assign-collection"
  | "assign-country"
  | "assign-product"
  | "unassign-category"
  | "unassign-collection"
  | "unassign-product"
  | "remove";
export type VoucherUrlQueryParams = Pagination &
  BulkAction &
  Dialog<VoucherUrlDialog> &
  ActiveTab<VoucherDetailsPageTab>;
export const voucherUrl = (id: string, params?: VoucherUrlQueryParams) =>
  voucherPath(encodeURIComponent(id)) + "?" + stringifyQs(params);
export const voucherAddPath = urlJoin(voucherSection, "add");
export const voucherAddUrl = voucherAddPath;
