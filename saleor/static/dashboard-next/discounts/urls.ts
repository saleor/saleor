import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { ActiveTab, Dialog, Pagination } from "../types";
import { SaleDetailsPageTab } from "./components/SaleDetailsPage";

export const discountSection = "/discounts/";

export const saleSection = urlJoin(discountSection, "sales");
export const saleListPath = saleSection;
export const saleListUrl = saleListPath;
export const salePath = (id: string) => urlJoin(saleSection, id);
export type SaleUrlDialog =
  | "assign-category"
  | "assign-collection"
  | "assign-product"
  | "remove";
export type SaleUrlQueryParams = Pagination &
  Dialog<SaleUrlDialog> &
  ActiveTab<SaleDetailsPageTab>;
export const saleUrl = (id: string, params?: SaleUrlQueryParams) =>
  salePath(encodeURIComponent(id)) + "?" + stringifyQs(params);
export const saleAddPath = urlJoin(saleSection, "add");
export const saleAddUrl = saleAddPath;

export const voucherSection = urlJoin(discountSection, "vouchers");
export const voucherListPath = voucherSection;
export const voucherListUrl = voucherListPath;
export const voucherPath = (id: string) => urlJoin(voucherSection, id);
export const voucherUrl = (id: string) => voucherPath(encodeURIComponent(id));
export const voucherAddPath = urlJoin(voucherSection, "add");
export const voucherAddUrl = voucherAddPath;
