import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { BulkAction, Dialog, Pagination } from "../types";

const collectionSectionUrl = "/collections/";

export const collectionListPath = collectionSectionUrl;
export type CollectionListUrlDialog = "publish" | "unpublish" | "remove";
export type CollectionListUrlQueryParams = BulkAction &
  Dialog<CollectionListUrlDialog> &
  Pagination;
export const collectionListUrl = (params?: CollectionListUrlQueryParams) =>
  collectionSectionUrl + "?" + stringifyQs(params);

export const collectionPath = (id: string) => urlJoin(collectionSectionUrl, id);
export type CollectionUrlDialog =
  | "remove"
  | "removeImage"
  | "assign"
  | "unassign";
export type CollectionUrlQueryParams = BulkAction &
  Pagination &
  Dialog<CollectionUrlDialog>;
export const collectionUrl = (id: string, params?: CollectionUrlQueryParams) =>
  collectionPath(encodeURIComponent(id)) + "?" + stringifyQs(params);

export const collectionAddPath = urlJoin(collectionSectionUrl, "add");
export const collectionAddUrl = collectionAddPath;
