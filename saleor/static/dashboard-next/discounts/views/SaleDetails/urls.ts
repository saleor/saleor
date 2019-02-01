import * as urlJoin from "url-join";

import { salePath } from "../../urls";

export const saleAssignProductsPath = (id: string) =>
  urlJoin(salePath(id), "assign-products");
export const saleAssignProductsUrl = (id: string) =>
  saleAssignProductsPath(encodeURIComponent(id));

export const saleAssignCategoriesPath = (id: string) =>
  urlJoin(salePath(id), "assign-categories");
export const saleAssignCategoriesUrl = (id: string) =>
  saleAssignCategoriesPath(encodeURIComponent(id));

export const saleAssignCollectionsPath = (id: string) =>
  urlJoin(salePath(id), "assign-collections");
export const saleAssignCollectionsUrl = (id: string) =>
  saleAssignCollectionsPath(encodeURIComponent(id));

export const saleDeletePath = (id: string) => urlJoin(salePath(id), "delete");
export const saleDeleteUrl = (id: string) =>
  saleDeletePath(encodeURIComponent(id));
