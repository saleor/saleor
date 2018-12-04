import * as urlJoin from "url-join";

const categorySectionUrl = "/categories/";

export const categoryListPath = categorySectionUrl;
export const categoryListUrl = categorySectionUrl;

export const categoryPath = (id: string) => urlJoin(categorySectionUrl, id);
export const categoryUrl = (id: string) => categoryPath(encodeURIComponent(id));

export const categoryAddPath = (parentId?: string) => {
  if (parentId) {
    return urlJoin(categoryPath(parentId), "add");
  }
  return urlJoin(categorySectionUrl, "add");
};
export const categoryAddUrl = (parentId?: string) =>
  categoryAddPath(encodeURIComponent(parentId));
