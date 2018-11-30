import * as urlJoin from "url-join";

const collectionSectionUrl = "/collections/";

export const collectionListPath = collectionSectionUrl;
export const collectionListUrl = collectionSectionUrl;

export const collectionPath = (id: string) => urlJoin(collectionSectionUrl, id);
export const collectionUrl = (id: string) =>
  collectionPath(encodeURIComponent(id));

export const collectionAddPath = urlJoin(collectionSectionUrl, "add");
export const collectionAddUrl = collectionAddPath;

export const collectionRemovePath = (id: string) =>
  urlJoin(collectionPath(id), "remove");
export const collectionRemoveUrl = (id: string) =>
  collectionRemovePath(encodeURIComponent(id));

export const collectionImageRemovePath = (id: string) =>
  urlJoin(collectionPath(id), "removeImage");
export const collectionImageRemoveUrl = (id: string) =>
  collectionImageRemovePath(encodeURIComponent(id));

export const collectionAddProductPath = (id: string) =>
  urlJoin(collectionPath(id), "add");
export const collectionAddProductUrl = (id: string) =>
  collectionAddProductPath(encodeURIComponent(id));
