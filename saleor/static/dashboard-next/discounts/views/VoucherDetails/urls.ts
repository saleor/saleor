import * as urlJoin from "url-join";

import { voucherPath } from "../../urls";

export const voucherAssignProductsPath = (id: string) =>
  urlJoin(voucherPath(id), "assign-products");
export const voucherAssignProductsUrl = (id: string) =>
  voucherAssignProductsPath(encodeURIComponent(id));

export const voucherAssignCategoriesPath = (id: string) =>
  urlJoin(voucherPath(id), "assign-categories");
export const voucherAssignCategoriesUrl = (id: string) =>
  voucherAssignCategoriesPath(encodeURIComponent(id));

export const voucherAssignCollectionsPath = (id: string) =>
  urlJoin(voucherPath(id), "assign-collections");
export const voucherAssignCollectionsUrl = (id: string) =>
  voucherAssignCollectionsPath(encodeURIComponent(id));

export const voucherAssignCountriesPath = (id: string) =>
  urlJoin(voucherPath(id), "assign-countries");
export const voucherAssignCountriesUrl = (id: string) =>
  voucherAssignCountriesPath(encodeURIComponent(id));

export const voucherDeletePath = (id: string) =>
  urlJoin(voucherPath(id), "delete");
export const voucherDeleteUrl = (id: string) =>
  voucherDeletePath(encodeURIComponent(id));
