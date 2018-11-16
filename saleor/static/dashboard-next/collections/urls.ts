import * as urlJoin from "url-join";

const collectionSectionUrl = "/collections/";
export const collectionListUrl = collectionSectionUrl;
export const collectionUrl = (id: string) => urlJoin(collectionSectionUrl, id);
export const collectionAddUrl = urlJoin(collectionSectionUrl, "add");
export const collectionRemoveUrl = (id: string) =>
  urlJoin(collectionUrl(id), "remove");
export const collectionImageRemoveUrl = (id: string) =>
  urlJoin(collectionUrl(id), "removeImage");
export const collectionAddProductUrl = (id: string) =>
  urlJoin(collectionUrl(id), "add");
