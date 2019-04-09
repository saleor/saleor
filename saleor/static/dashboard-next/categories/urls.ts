import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { ActiveTab, Dialog, Pagination } from "../types";
import { CategoryPageTab } from "./components/CategoryUpdatePage";

const categorySectionUrl = "/categories/";

export const categoryListPath = categorySectionUrl;
export const categoryListUrl = categorySectionUrl;

export const categoryPath = (id: string) => urlJoin(categorySectionUrl, id);
export type CategoryUrlQueryParams = Dialog<"delete"> &
  Pagination &
  ActiveTab<CategoryPageTab>;
export const categoryUrl = (id: string, params?: CategoryUrlQueryParams) =>
  categoryPath(encodeURIComponent(id)) + "?" + stringifyQs(params);

export const categoryAddPath = (parentId?: string) => {
  if (parentId) {
    return urlJoin(categoryPath(parentId), "add");
  }
  return urlJoin(categorySectionUrl, "add");
};
export const categoryAddUrl = (parentId?: string) =>
  categoryAddPath(parentId ? encodeURIComponent(parentId) : undefined);
