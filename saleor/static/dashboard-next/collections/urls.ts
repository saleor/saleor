import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { Dialog, Pagination } from "../types";

const collectionSectionUrl = "/collections/";

export const collectionListPath = collectionSectionUrl;
export const collectionListUrl = collectionSectionUrl;

export const collectionPath = (id: string) => urlJoin(collectionSectionUrl, id);
export type CollectionUrlDialog = "remove" | "removeImage" | "assign";
export type CollectionUrlQueryParams = Pagination & Dialog<CollectionUrlDialog>;
export const collectionUrl = (id: string, params?: CollectionUrlQueryParams) =>
  collectionPath(encodeURIComponent(id)) + "?" + stringifyQs(params);

export const collectionAddPath = urlJoin(collectionSectionUrl, "add");
export const collectionAddUrl = collectionAddPath;
