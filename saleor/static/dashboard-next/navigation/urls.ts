import { stringify as stringifyQs } from "qs";
import urlJoin from "url-join";

import { BulkAction, Dialog, Pagination, SingleAction } from "../types";

export const navigationSection = "/navigation";

export const menuListPath = navigationSection;
export type MenuListUrlDialog = "add" | "remove" | "remove-many";
export type MenuListUrlQueryParams = BulkAction &
  Dialog<MenuListUrlDialog> &
  Pagination &
  SingleAction;
export const menuListUrl = (params?: MenuListUrlQueryParams) =>
  menuListPath + "?" + stringifyQs(params);

export const menuPath = (id: string) => urlJoin(navigationSection, id);
export type MenuUrlDialog = "add-item" | "edit-item" | "remove";
export type MenuUrlQueryParams = Dialog<MenuUrlDialog> & SingleAction;
export const menuUrl = (id: string, params?: MenuUrlQueryParams) =>
  menuPath(encodeURIComponent(id)) + "?" + stringifyQs(params);
