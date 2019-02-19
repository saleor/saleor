import * as urlJoin from "url-join";

export const pagesSection = "/pages/";

export const pageListPath = pagesSection;
export const pageListUrl = pageListPath;

export const pagePath = (id: string) => urlJoin(pagesSection, id);
export const pageUrl = (id: string) => pagePath(encodeURIComponent(id));

export const pageCreatePath = urlJoin(pagesSection, "add");
export const pageCreateUrl = pageCreatePath;

export const pageRemovePath = (id: string) => urlJoin(pagePath(id), "remove");
export const pageRemoveUrl = (id: string) =>
  pageRemovePath(encodeURIComponent(id));
