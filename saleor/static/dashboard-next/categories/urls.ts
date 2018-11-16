import * as urlJoin from "url-join";

const categorySectionUrl = "/categories/";
export const categoryListUrl = categorySectionUrl;
export const categoryUrl = (id: string) => urlJoin(categorySectionUrl, id);
export const categoryAddUrl = (parentId?: string) => {
  if (parentId) {
    return urlJoin(categoryUrl(parentId), "add");
  }
  return urlJoin(categorySectionUrl, "add");
};
