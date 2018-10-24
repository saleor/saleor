export const collectionListUrl = "/collections/";
export const collectionUrl = (id: string) => "/collections/" + id + "/";
export const collectionAddUrl = "/collections/add/";
export const collectionRemoveUrl = (id: string) =>
  collectionUrl(id) + "remove/";
export const collectionImageRemoveUrl = (id: string) =>
  collectionUrl(id) + "removeImage/";
export const collectionAddProductUrl = (id: string) =>
  collectionUrl(id) + "add/";
